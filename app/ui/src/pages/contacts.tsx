import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { useUser } from "@/context/user-context";
import { ContactsAPI } from "@/api/contact";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Star, Trash2, Ban, UserPlus } from "lucide-react";
import type { UserDto } from "@/models/dto";
import { RoomsAPI } from "@/api/rooms";
import { useChatWs } from "@/context/websocket-context";

export const ContactsPage = () => {
	const { token, user } = useUser();
	const { rooms } = useChatWs();
	const navigate = useNavigate();
	const [contacts, setContacts] = useState<UserDto[]>([]);
	const [favorites, setFavorites] = useState<UserDto[]>([]);
	const [blocked, setBlocked] = useState<UserDto[]>([]);
	const [loading, setLoading] = useState(true);
	const [search, setSearch] = useState("");
	const [newContactUsername, setNewContactUsername] = useState("");
	const [addingContact, setAddingContact] = useState(false);

	useEffect(() => {
		if (token) {
			try {
				const payload = JSON.parse(atob(token.split('.')[1]));
				console.log("JWT Token Payload:", payload);
			} catch (e) {
				console.error("Failed to decode token:", e);
			}
		}
	}, [token]);

	const fetchAll = useCallback(async () => {
		if (!token) return;
		setLoading(true);
		try {
			const [contactsData, favoritesData, blockedData] = await Promise.all([
				ContactsAPI.getContacts(token),
				ContactsAPI.getFavorites(token),
				ContactsAPI.getBlocked(token),
			]);
			setContacts(contactsData);
			setFavorites(favoritesData);
			setBlocked(blockedData);
		} catch (error) {
			console.error("Failed to fetch contacts:", error);
		}
		setLoading(false);
	}, [token]);

	useEffect(() => {
		fetchAll();
	}, [fetchAll]);

	const handleAddContact = async () => {
		if (!token || !newContactUsername.trim()) return;
		setAddingContact(true);
		try {
			await ContactsAPI.addContact(token, newContactUsername.trim());
			setNewContactUsername("");
			await fetchAll();
		} catch (error) {
			console.error("Failed to add contact:", error);
			alert("Failed to add contact");
		}
		setAddingContact(false);
	};

	const handleDeleteContact = async (contactId: string) => {
		if (!token) return;
		try {
			await ContactsAPI.deleteContact(token, contactId);
			await fetchAll();
		} catch (error) {
			console.error("Failed to delete contact:", error);
			alert("Failed to delete contact");
		}
	};

	const handleToggleFavorite = async (contactId: string) => {
		if (!token) return;
		try {
			await ContactsAPI.toggleFavorite(token, contactId);
			await fetchAll();
		} catch (error) {
			console.error("Failed to toggle favorite:", error);
		}
	};

	const handleToggleBlockUser = async (contactId: string) => {
		if (!token) return;
		try {
			await ContactsAPI.toggleBlockUser(token, contactId);
			await fetchAll();
		} catch (error) {
			console.error("Failed to block user:", error);
		}
	};

	const handleOpenDirectMessage = async (contactId: string) => {
		if (!token || !user?.userId) return;
		try {
			const existingRoom = rooms.find(room => {
				if (room.roomType !== "direct") return false;

				const participantIds = room.participants?.map(p => p.userId) || [];
				return participantIds.length === 2 &&
					participantIds.includes(user.userId) &&
					participantIds.includes(contactId);
			});

			if (existingRoom) {
				navigate(`/rooms/${existingRoom.id}`);
			} else {
				const roomId = await RoomsAPI.createRoom(token, "direct", [contactId]);
				navigate(`/rooms/${roomId}`);
			}
		} catch (error) {
			console.error("Failed to create direct message room:", error);
			alert("Failed to open direct message");
		}
	};

	const filteredContacts = contacts.filter(
		(contact) =>
			(contact.username?.toLowerCase() || contact.nickname?.toLowerCase() || "").includes(search.toLowerCase()) ||
			(contact.email?.toLowerCase() || contact.nickname?.toLowerCase() || "").includes(search.toLowerCase())
	);

	const renderContactList = (contactsList: UserDto[], showActions = true) => (
		<ul className="space-y-2">
			{contactsList.map((contact) => (
				<li
					key={contact.userId}
					className="flex items-center justify-between p-3 rounded-md bg-muted hover:bg-accent transition"
				>
					<div
						className="flex-1 cursor-pointer"
						onClick={() => handleOpenDirectMessage(contact.userId)}
					>
						<div className="font-medium">{contact.nickname || contact.username}</div>
						{contact.email && (
							<div className="text-xs text-muted-foreground">{contact.email}</div>
						)}
					</div>
					{showActions && (
						<div className="flex gap-2">
							<Button
								size="sm"
								variant={contact.isFavorite ? "default" : "outline"}
								onClick={() => handleToggleFavorite(contact.userId)}
								title={contact.isFavorite ? "Remove from favorites" : "Add to favorites"}
							>
								<Star className={`h-4 w-4 ${contact.isFavorite ? "fill-current" : ""}`} />
							</Button>
							{!contact.isBlocked && (
								<Button
									size="sm"
									variant="outline"
									onClick={() => handleToggleBlockUser(contact.userId)}
									title="Block user"
								>
									<Ban className="h-4 w-4" />
								</Button>
							)}
							<Button
								size="sm"
								variant="destructive"
								onClick={() => handleDeleteContact(contact.userId)}
								title="Delete contact"
							>
								<Trash2 className="h-4 w-4" />
							</Button>
						</div>
					)}
				</li>
			))}
		</ul>
	);

	if (loading) {
		return (
			<div className="flex justify-center items-center h-screen">
				<Spinner className="size-16" />
			</div>
		);
	}

	return (
		<div className="max-w-md md:max-w-xl lg:max-w-4xl mx-auto mt-8 p-4 bg-background dark:bg-neutral-800 rounded-lg shadow">
			<h1 className="text-2xl font-bold mb-4">Contacts</h1>

			{/* Add Contact Section */}
			<div className="flex gap-2 mb-4">
				<Input
					id="new-contact-id"
					name="newContactId"
					placeholder="Enter username to add contact..."
					value={newContactUsername}
					onChange={(e) => setNewContactUsername(e.target.value)}
					onKeyDown={(e) => e.key === "Enter" && handleAddContact()}
					className="flex-1"
				/>
				<Button onClick={handleAddContact} disabled={addingContact || !newContactUsername.trim()}>
					<UserPlus className="h-4 w-4 mr-2" />
					Add
				</Button>
			</div>

			<Separator className="mb-4" />

			<Tabs defaultValue="all" className="w-full">
				<TabsList className="grid w-full grid-cols-3">
					<TabsTrigger value="all">All ({contacts.length})</TabsTrigger>
					<TabsTrigger value="favorites">Favorites ({favorites.length})</TabsTrigger>
					<TabsTrigger value="blocked">Blocked ({blocked.length})</TabsTrigger>
				</TabsList>

				<TabsContent value="all" className="mt-4">
					<Input
						id="search-contacts"
						name="search"
						placeholder="Search contacts..."
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						className="mb-4"
					/>
					{filteredContacts.length === 0 ? (
						<div className="text-center text-muted-foreground py-8">
							No contacts found.
						</div>
					) : (
						renderContactList(filteredContacts)
					)}
				</TabsContent>

				<TabsContent value="favorites" className="mt-4">
					{favorites.length === 0 ? (
						<div className="text-center text-muted-foreground py-8">
							No favorite contacts yet.
						</div>
					) : (
						renderContactList(favorites)
					)}
				</TabsContent>

				<TabsContent value="blocked" className="mt-4">
					{blocked.length === 0 ? (
						<div className="text-center text-muted-foreground py-8">
							No blocked users.
						</div>
					) : (
						<ul className="space-y-2">
							{blocked.map((contact) => (
								<li
									key={contact.userId}
									className="flex items-center justify-between p-3 rounded-md bg-muted"
								>
									<div>
										<div className="font-medium">{contact.nickname || contact.username}</div>
										{contact.email && (
											<div className="text-xs text-muted-foreground">{contact.email}</div>
										)}
									</div>
									<Button
										size="sm"
										variant="outline"
										onClick={() => handleToggleBlockUser(contact.userId)}
									>
										Unblock
									</Button>
								</li>
							))}
						</ul>
					)}
				</TabsContent>
			</Tabs>
		</div>
	);
};
