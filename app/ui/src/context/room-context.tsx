/* eslint-disable react-refresh/only-export-components */
import type { RoomDto, RoomUserDto, UserDto } from '@/models/dto';
import { RoomsAPI } from '@/api/rooms';
import React, { createContext, useContext, useState, useCallback } from 'react';

interface RoomContextType {
	room: RoomDto | null;
	setRoom: (room: RoomDto | null) => void;
	getTitle: (user: UserDto) => string;
	users: RoomUserDto[];
	loadUsers: (token: string, roomId: string) => Promise<void>;
	getUserById: (userId: string) => RoomUserDto | undefined;
}

const RoomContext = createContext<RoomContextType | undefined>(undefined);

export const RoomProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [room, setRoom] = useState<RoomDto | null>(null);
	const [users, setUsers] = useState<RoomUserDto[]>([]);

	const loadUsers = useCallback(async (token: string, roomId: string) => {
		try {
			const roomUsers = await RoomsAPI.getUsers(token, roomId);
			setUsers(roomUsers);
		} catch (error) {
			console.error("Failed to load room users:", error);
			setUsers([]);
		}
	}, []);

	const getUserById = useCallback((userId: string) => {
		return users.find(user => user.id === userId);
	}, [users]);

	const getTitle = useCallback((user: UserDto): string => {
		if (!room) return "Loading...";

		if (room.roomType === "direct") {
			// Find the other user in the direct message
			const otherUserId = room.participants.find(p => p.userId !== user?.userId)?.userId
				|| (room.createdBy !== user?.userId ? room.createdBy : room.participants[0]?.userId);

			const otherUser = users.find(u => u.id === otherUserId);
			return otherUser?.name || "Direct Message";
		}

		return room.name || "Unnamed Room";
	}, [room, users]);

	return (
		<RoomContext.Provider value={{ room, setRoom, getTitle, users, loadUsers, getUserById }}>
			{children}
		</RoomContext.Provider>
	);
};

export const useRoom = () => {
	const context = useContext(RoomContext);
	if (!context) throw new Error("useRoom must be used within a RoomProvider");
	return context;
};
