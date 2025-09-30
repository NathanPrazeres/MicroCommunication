import { useEffect, useState, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router";
import { useChatWs } from "@/context/websocket-context";
import { useUser } from "@/context/user-context";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Skeleton } from "@/components/ui/skeleton";
import { useRoom } from "@/context/room-context";
import { LogOut } from "lucide-react";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export const RoomMessagesPage = () => {
	const { roomId } = useParams<{ roomId: string }>();
	const { rooms, messages, sendMessage, markAsRead, loadMessages, leaveRoom } = useChatWs();
	const { user, token } = useUser();
	const { room, setRoom, getTitle, loadUsers, getUserById } = useRoom();
	const [loading, setLoading] = useState(true);
	const [input, setInput] = useState("");
	const [leaving, setLeaving] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);
	const navigate = useNavigate();

	// Sync room context with url
	useEffect(() => {
		if (!roomId) {
			setRoom(null);
			return;
		}
		const currentRoom = rooms.find(r => r.id === roomId);
		if (currentRoom) {
			setRoom(currentRoom);
			// Load room users whenever the room changes
			if (token) {
				loadUsers(token, roomId);
			}
		}
	}, [roomId, setRoom, rooms, token, loadUsers]);

	// Fetch old messages from the API
	useEffect(() => {
		if (!roomId) return;
		setLoading(true);
		loadMessages(roomId).finally(() => setLoading(false));
		markAsRead(roomId);
	}, [roomId, loadMessages, markAsRead]);

	const allMessages = useMemo(
		() => (roomId ? messages[roomId] || [] : []),
		[roomId, messages]
	);

	// Mark room as read whenever a message comes in while it's open
	useEffect(() => {
		if (!roomId || allMessages.length === 0) return;
		markAsRead(roomId);
	}, [allMessages.length, roomId, markAsRead]);

	// Auto-scroll to bottom when new messages arrive
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [allMessages]);

	const handleSend = () => {
		if (!roomId || !input.trim()) return;
		sendMessage(roomId, input.trim());
		setInput("");
	};

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	};

	const handleLeaveRoom = async () => {
		if (!roomId || !user) return;
		setLeaving(true);
		try {
			await leaveRoom(user.userId, roomId);
			navigate("/rooms");
		} catch (error) {
			console.error("Failed to leave room:", error);
			alert("Failed to leave room. Please try again.");
		}
		setLeaving(false);
	};

	if (loading) {
		return (
			<div className="flex flex-col justify-center items-center h-screen gap-4 px-6">
				<Skeleton className="h-[48px] w-full max-w-md lg:max-w-lg rounded-xl self-end" />
				<Skeleton className="h-[48px] w-full max-w-md lg:max-w-lg rounded-xl self-start" />
				<Spinner className="size-16 my-6 text-neutral-700 dark:text-gray-400" />
			</div>
		);
	}

	return (
		<div className="flex flex-col h-[calc(100vh-5rem)] w-full px-6">
			{/* Title bar */}
			<div className="border-b bg-background px-6 py-3 flex items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<h2 className="text-xl font-semibold">{user ? getTitle(user) : ""}</h2>
				</div>

				<AlertDialog>
					<AlertDialogTrigger asChild>
						<Button variant="ghost" size="icon" disabled={leaving}>
							<LogOut className="h-5 w-5" />
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Leave Room?</AlertDialogTitle>
							<AlertDialogDescription>
								Are you sure you want to leave this room? You won't be able to see messages or rejoin without being invited again.
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>Cancel</AlertDialogCancel>
							<AlertDialogAction onClick={handleLeaveRoom}>
								Leave Room
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</div>

			{/* Messages area */}
			<div className="flex-1 overflow-y-auto py-4 space-y-3 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-gray-700 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-gray-600">
				{allMessages.length === 0 ? (
					<div className="text-center text-muted-foreground">No messages yet.</div>
				) : (
					allMessages.map((msg) => (
						<div
							key={msg.id}
							className={`mx-2 flex ${msg.senderId === user?.userId ? "justify-end" : "justify-start"}`}
						>
							<div
								className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${msg.senderId === user?.userId
									? "bg-primary text-primary-foreground"
									: "bg-muted"
									}`}
							>
								{msg.senderId !== user?.userId && room?.roomType !== "direct" && (
									<div className="text-xs text-start font-bold font-medium opacity-80 mb-1">
										{getUserById(msg.senderId)?.name || "Unknown User"}
									</div>
								)}
								<div className="text-start text-sm font-normal break-words whitespace-pre-wrap">{msg.content}</div>
								<div
									className={`text-xs opacity-70 mt-1 ${msg.senderId === user?.userId ? "text-end" : "text-start"}`}
								>
									{new Date(msg.createdAt).toLocaleTimeString()}
								</div>
							</div>
						</div>
					))
				)}
				<div ref={messagesEndRef} />
			</div>

			{/* Input area */}
			<div className="border-t py-4">
				<div className="flex gap-2 max-w-4xl mx-auto">
					<Input
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyDown={handleKeyDown}
						placeholder="Type a message..."
						className="flex-1"
					/>
					<Button onClick={handleSend} disabled={!input.trim()}>
						Send
					</Button>
				</div>
			</div>
		</div>
	);
};
