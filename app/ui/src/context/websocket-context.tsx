/* eslint-disable react-refresh/only-export-components */
import { getChatService } from "@/config";
import { normalizeEnvelope } from "@/models/normalize";
import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useUser } from "./user-context";
import { RoomsAPI } from "@/api/rooms";
import type { UnreadMap } from "@/models/info";
import type { MessageDto, RoomDto } from "@/models/dto";

const WebSocketContext = createContext<{
	rooms: RoomDto[];
	unread: UnreadMap;
	markAsRead: (roomId: string) => Promise<void>;
	sendMessage: (roomId: string, content: string, replyToId?: string) => void;
	messages: { [roomId: string]: MessageDto[] };
	loadMessages: (roomId: string) => Promise<void>;
	readyState: ReadyState;
	reconnect: () => void;
	addRoom: (room: RoomDto) => void;
	leaveRoom: (userId: string, roomId: string) => Promise<void>;
} | null>(null);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [rooms, setRooms] = useState<RoomDto[]>([]);
	const [unread, setUnread] = useState<UnreadMap>({});
	const [messages, setMessages] = useState<{ [roomId: string]: MessageDto[] }>({});
	const [loadedRooms, setLoadedRooms] = useState<Set<string>>(new Set());
	const [shouldConnect, setShouldConnect] = useState(true);
	const { token } = useUser();

	const WS_URL = useMemo(() => {
		if (!token || !shouldConnect) return null;
		return `ws://${getChatService()}/api/v1/ws?token=${encodeURIComponent(token)}`;
	}, [token, shouldConnect]);

	const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(WS_URL, {
		shouldReconnect: () => shouldConnect,
		reconnectAttempts: 3,
		reconnectInterval: 3000,
		retryOnError: true,
		onOpen: () => console.debug("Opened WebSocket:", WS_URL),
		onClose: () => console.debug("WebSocket Closed"),
	});

	// Manual reconnect - toggle connection off and back on
	const reconnect = useCallback(() => {
		console.debug("Manually reconnecting WebSocket...");
		setShouldConnect(false);
		// Use setTimeout to ensure the disconnect happens before reconnect
		setTimeout(() => {
			setShouldConnect(true);
		}, 100);
	}, []);

	// Fetch initial rooms + unread counts when token is available
	useEffect(() => {
		if (!token) return;
		const fetchRooms = async () => {
			try {
				const roomsData = await RoomsAPI.getRooms(token);
				setRooms(roomsData);
				const counts: UnreadMap = {};
				roomsData.forEach((room: RoomDto) => {
					counts[room.id] = room.unreadCount;
				});
				setUnread(counts);
			} catch (e) {
				console.error("Failed to fetch rooms", e);
			}
		};
		fetchRooms();
	}, [token]);

	// Lazy Load old messages for a room (HTTP GET, only once per room)
	const loadMessages = useCallback(
		async (roomId: string) => {
			if (!token || loadedRooms.has(roomId)) return; // already loaded
			try {
				const messagesData = await RoomsAPI.getMessages(token, roomId);
				setMessages((prev) => ({
					...prev,
					[roomId]: messagesData,
				}));
				setLoadedRooms((prev) => new Set(prev).add(roomId));
			} catch (e) {
				console.error(`Failed to load messages for room ${roomId}:`, e);
			}
		},
		[token, loadedRooms]
	);

	const addRoom = useCallback((room: RoomDto) => {
		setRooms(prev => [...prev, room]);
		setUnread(prev => ({ ...prev, [room.id]: room.unreadCount }));
	}, [setRooms]);

	useEffect(() => {
		if (!lastJsonMessage) return;
		const msg = normalizeEnvelope(lastJsonMessage);
		if (!msg) return;

		switch (msg.type) {
			case "error": {
				console.error(msg.data)
				break;
			}
			case "control": {
				const { roomId, status } = msg.data;

				if (status === "added") {
					// Fetch new room details and add to list
					if (!token) break;
					RoomsAPI.getRoom(token, roomId)
						.then(room => {
							setRooms(prev => [...prev, room]);
							setUnread(prev => ({ ...prev, [roomId]: 0 }));
						})
						.catch(e => console.error("Failed to fetch new room", e));
				} else if (status === "removed") {
					// Remove room from list
					setRooms(prev => prev.filter(r => r.id !== roomId));
					setUnread(prev => {
						const copy = { ...prev };
						delete copy[roomId];
						return copy;
					});
					setMessages(prev => {
						const copy = { ...prev };
						delete copy[roomId];
						return copy;
					});
				} else if (status === "promoted" || status === "demoted") {
					// Could update room role/permissions here if needed
					console.debug(`User ${status} in room ${roomId}`);
				}
				break;
			}
			case "send_response": {
				const m = msg.data.message;
				if (m) {
					setMessages((prev) => ({
						...prev,
						[m.roomId]: [...(prev[m.roomId] || []), m]
					}));
				}
				break;
			}
			case "message": {
				const data = msg.data;
				setUnread((prev: UnreadMap) => ({
					...prev,
					[data.roomId]: (prev[data.roomId] ?? 0) + 1
				}));
				setMessages((prev) => ({
					...prev,
					[data.roomId]: [
						...(prev[data.roomId] || []),
						data
					]
				}));
				break;
			}
		}
	}, [lastJsonMessage, token]);

	const markAsRead = useCallback(async (roomId: string) => {
		if (!token) return;
		try {
			await RoomsAPI.markAsRead(token, roomId);
			setUnread((prev) => ({ ...prev, [roomId]: 0 }));
		} catch (e) {
			console.error("Failed to mark room as read", roomId, e);
		}
	}, [token]);

	const sendMessage = (roomId: string, content: string, replyToId?: string) => {
		sendJsonMessage({
			type: "send_message",
			data: {
				room_id: roomId,
				content: content,
				reply_to_id: replyToId ?? null
			}
		});
	};

	const leaveRoom = useCallback(async (userId: string, roomId: string) => {
		if (!token) return;
		try {
			await RoomsAPI.removeUser(token, roomId, userId);
			// Remove room from local state
			setRooms(prev => prev.filter(r => r.id !== roomId));
			// Remove messages for that room
			setMessages(prev => {
				const updated = { ...prev };
				delete updated[roomId];
				return updated;
			});
			// Remove unread count
			setUnread(prev => {
				const updated = { ...prev };
				delete updated[roomId];
				return updated;
			});
		} catch (error) {
			console.error("Failed to leave room:", error);
			throw error;
		}
	}, [token]);

	return (
		<WebSocketContext.Provider value={{ rooms, unread, markAsRead, sendMessage, messages, loadMessages, readyState, reconnect, addRoom, leaveRoom }}>
			{children}
		</WebSocketContext.Provider>
	);
};

export const useChatWs = () => {
	const context = useContext(WebSocketContext);
	if (!context) throw new Error("useChatWs must be used within a WebSocketProvider");
	return context;
};
