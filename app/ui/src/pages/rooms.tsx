import { useCallback, useEffect, useState } from "react";
import { useUser } from "@/context/user-context";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useChatWs } from "@/context/websocket-context";
import { useNavigate } from "react-router";
import { UsersAPI } from "@/api/users";
import type { RoomDto } from "@/models/dto";
import { Button } from "@/components/ui/button";
import { MessageCirclePlus } from "lucide-react";

export const ChatRoomsPage = () => {
	const { token, user, loading } = useUser();
	const { rooms, unread } = useChatWs();
	const [filteredRooms, setFilteredRooms] = useState(rooms);
	const [search, setSearch] = useState<string>("");
	const [directRoomNames, setDirectRoomNames] = useState<Record<string, string>>({});
	const navigate = useNavigate();

	// Load direct room names
	useEffect(() => {
		const loadDirectRoomNames = async () => {
			if (!token || !user) return;

			const names: Record<string, string> = {};

			for (const room of rooms) {
				if (room.roomType === "direct") {
					try {
						// Find the other user's ID
						const otherUserId = room.participants.find(p => p.userId !== user.userId)?.userId
							|| (room.createdBy !== user.userId ? room.createdBy : room.participants[0]?.userId);

						if (otherUserId) {
							const otherUser = await UsersAPI.getUser(token, otherUserId);
							names[room.id] = otherUser.username || otherUser.email;
						}
					} catch (error) {
						console.error(`Failed to load user for room ${room.id}:`, error);
						names[room.id] = "Unknown User";
					}
				}
			}
			setDirectRoomNames(names);
		};

		loadDirectRoomNames();
	}, [rooms, token, user]);

	const getRoomDisplayName = useCallback((room: RoomDto): string => {
		if (room.roomType !== "direct") {
			return room.name || "Unnamed Room";
		}
		return directRoomNames[room.id] || "Loading...";
	}, [directRoomNames]);

	// Update filtered rooms when rooms or search changes
	useEffect(() => {
		if (!search) {
			setFilteredRooms(rooms);
		} else {
			setFilteredRooms(
				rooms.filter(room => {
					const displayName = getRoomDisplayName(room);
					return displayName.toLowerCase().includes(search.toLowerCase());
				})
			);
		}
	}, [search, rooms, directRoomNames, getRoomDisplayName]);

	return (
		<div className="max-w-md md:max-w-xl lg:max-w-4xl mx-auto mt-8 p-4 bg-background dark:bg-neutral-800 rounded-lg shadow">
			<div className="relative mb-4">
				<h1 className="text-2xl font-bold text-center">Your Chat Rooms</h1>
				<Button
					variant="outline"
					className="absolute right-0 top-1/2 -translate-y-1/2"
					onClick={() => navigate("/rooms/new")}
				>
					<MessageCirclePlus />
				</Button>
			</div>
			<Input
				placeholder="Search rooms..."
				value={search}
				onChange={e => setSearch(e.target.value)}
				className="mb-4"
			/>
			<Separator className="mb-4" />
			{loading ? (
				<div className="flex justify-center items-center h-32">
					<Spinner />
				</div>
			) : filteredRooms.length === 0 ? (
				<div className="text-center text-muted-foreground">No rooms found.</div>
			) : (
				<ul className="space-y-2">
					{filteredRooms.map(room => (
						<li
							key={room.id}
							className="flex items-center justify-between p-3 rounded-md bg-muted hover:bg-accent transition cursor-pointer"
							onClick={() => { navigate(`/rooms/${room.id}`); }}
						>
							<span className="font-medium">{getRoomDisplayName(room)}</span>
							{unread[room.id] > 0 && (
								<span className="ml-2 px-2 py-1 text-xs bg-primary text-primary-foreground rounded-full">
									{unread[room.id]}
								</span>
							)}
						</li>
					))}
				</ul>
			)}
		</div>
	);
};
