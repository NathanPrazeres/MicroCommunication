import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { useUser } from "@/context/user-context";
import { ContactsAPI } from "@/api/contact";
import { RoomsAPI } from "@/api/rooms";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Users, MessageSquare, ArrowLeft } from "lucide-react";
import type { UserDto } from "@/models/dto";
import { useRoom } from "@/context/room-context";
import { useChatWs } from "@/context/websocket-context";

export const NewRoomPage = () => {
	const { token } = useUser();
	const { setRoom } = useRoom();
	const { addRoom } = useChatWs();
	const navigate = useNavigate();

	const [roomType, setRoomType] = useState<"direct" | "group" | "channel">("group");
	const [name, setName] = useState("");
	const [description, setDescription] = useState("");
	const [contacts, setContacts] = useState<UserDto[]>([]);
	const [selectedParticipants, setSelectedParticipants] = useState<string[]>([]);
	const [loading, setLoading] = useState(true);
	const [creating, setCreating] = useState(false);
	const [search, setSearch] = useState("");

	useEffect(() => {
		if (!token) return;
		const fetchContacts = async () => {
			try {
				const contactsData = await ContactsAPI.getContacts(token);
				setContacts(contactsData.filter(c => !c.isBlocked));
			} catch (error) {
				console.error("Failed to fetch contacts:", error);
			}
			setLoading(false);
		};
		fetchContacts();
	}, [token]);

	const handleToggleParticipant = (userId: string) => {
		setSelectedParticipants(prev =>
			prev.includes(userId)
				? prev.filter(id => id !== userId)
				: [...prev, userId]
		);
	};

	const handleCreateRoom = async () => {
		if (!token) return;

		// Validation
		if (roomType === "direct" && selectedParticipants.length !== 1) {
			alert("Direct messages must have exactly 1 participant");
			return;
		}
		if ((roomType === "group") && !name.trim()) {
			alert("Group rooms must have a name");
			return;
		}
		if (roomType === "group" && selectedParticipants.length === 0) {
			alert("Group rooms must have at least 1 participant");
			return;
		}

		setCreating(true);
		try {
			const roomId = await RoomsAPI.createRoom(
				token,
				roomType,
				selectedParticipants,
				name || undefined,
				description || undefined
			);

			const newRoom = await RoomsAPI.getRoom(token, roomId);
			addRoom(newRoom)
			setRoom(newRoom);
			navigate(`/rooms/${roomId}`);
		} catch (error) {
			console.error("Failed to create room:", error);
			alert("Failed to create room");
		}
		setCreating(false);
	};

	const filteredContacts = contacts.filter(contact =>
		(contact.nickname || contact.username).toLowerCase().includes(search.toLowerCase()) ||
		contact.email.toLowerCase().includes(search.toLowerCase())
	);

	return (
		<div className="max-w-2xl mx-auto mt-8 p-4">
			<Button
				variant="ghost"
				className="mb-4"
				onClick={() => navigate("/rooms")}
			>
				<ArrowLeft className="mr-2 h-4 w-4" />
				Back to Rooms
			</Button>

			<Card>
				<CardHeader>
					<CardTitle className="text-2xl">Create New Room</CardTitle>
					<CardDescription>
						Start a new conversation with your contacts
					</CardDescription>
				</CardHeader>
				<CardContent>
					<Tabs value={roomType} onValueChange={(v) => setRoomType(v as typeof roomType)}>
						<TabsList className="grid w-full grid-cols-2">
							<TabsTrigger value="direct">
								<MessageSquare className="mr-2 h-4 w-4" />
								Direct
							</TabsTrigger>
							<TabsTrigger value="group">
								<Users className="mr-2 h-4 w-4" />
								Group
							</TabsTrigger>
						</TabsList>

						<TabsContent value="direct" className="space-y-4">
							<p className="text-sm text-muted-foreground">
								Start a private conversation with one contact
							</p>
						</TabsContent>

						<TabsContent value="group" className="space-y-4">
							<div className="space-y-2">
								<Label htmlFor="group-name">Group Name *</Label>
								<Input
									id="group-name"
									placeholder="My Awesome Group"
									value={name}
									onChange={(e) => setName(e.target.value)}
								/>
							</div>
							<div className="space-y-2">
								<Label htmlFor="group-description">Description</Label>
								<Textarea
									id="group-description"
									placeholder="What's this group about?"
									value={description}
									onChange={(e) => setDescription(e.target.value)}
								/>
							</div>
						</TabsContent>
					</Tabs>

					<Separator className="my-6" />

					<div className="space-y-4">
						<div>
							<Label>
								{roomType === "direct" ? "Select Contact *" : "Select Participants"}
							</Label>
							<p className="text-sm text-muted-foreground mb-2">
								{roomType === "direct"
									? "Choose one contact for a direct message"
									: roomType === "group"
										? "Add people to your group"
										: "Add initial members to your channel"}
							</p>
						</div>

						<Input
							placeholder="Search contacts..."
							value={search}
							onChange={(e) => setSearch(e.target.value)}
						/>

						{loading ? (
							<div className="flex justify-center py-8">
								<Spinner />
							</div>
						) : filteredContacts.length === 0 ? (
							<div className="text-center text-muted-foreground py-8">
								{search ? "No contacts found" : "You don't have any contacts yet"}
							</div>
						) : (
							<div className="border rounded-md max-h-64 overflow-y-auto">
								<div className="divide-y">
									{filteredContacts.map((contact) => (
										<label
											key={contact.userId}
											className="flex items-center gap-3 p-3 hover:bg-accent cursor-pointer"
										>
											<Checkbox
												checked={selectedParticipants.includes(contact.userId)}
												onCheckedChange={() => handleToggleParticipant(contact.userId)}
												disabled={roomType === "direct" && selectedParticipants.length === 1 && !selectedParticipants.includes(contact.userId)}
											/>
											<div className="flex-1">
												<div className="font-medium">
													{contact.nickname || contact.username}
												</div>
												<div className="text-xs text-muted-foreground">
													{contact.email}
												</div>
											</div>
										</label>
									))}
								</div>
							</div>
						)}

						{selectedParticipants.length > 0 && (
							<div className="text-sm text-muted-foreground">
								{selectedParticipants.length} participant{selectedParticipants.length !== 1 ? "s" : ""} selected
							</div>
						)}
					</div>

					<div className="flex gap-2 mt-6">
						<Button
							className="flex-1"
							onClick={handleCreateRoom}
							disabled={creating || (roomType === "direct" && selectedParticipants.length !== 1)}
						>
							{creating ? (
								<>
									<Spinner className="mr-2 h-4 w-4" />
									Creating...
								</>
							) : (
								"Create Room"
							)}
						</Button>
						<Button
							variant="outline"
							onClick={() => navigate("/rooms")}
							disabled={creating}
						>
							Cancel
						</Button>
					</div>
				</CardContent>
			</Card>
		</div>
	);
};
