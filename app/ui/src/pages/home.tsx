import { useNavigate } from "react-router";
import { useUser } from "@/context/user-context";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { MessageSquare, Users, Plus, Search } from "lucide-react";

export const HomePage = () => {
	const navigate = useNavigate();
	const { user } = useUser();

	return (
		<div className="min-h-screen bg-gradient-to-br from-background to-muted">
			<div className="container mx-auto px-4 py-16">
				{/* Welcome Section */}
				<div className="text-center mb-12">
					<h1 className="text-4xl md:text-5xl font-bold mb-4">
						Welcome{user ? ` back, ${user.username}` : ""}! 👋
					</h1>
					<p className="text-xl text-muted-foreground">
						Connect with friends and start conversations
					</p>
				</div>

				{/* Action Cards */}
				<div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
					{/* Rooms Card */}
					<Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate("/rooms")}>
						<CardHeader>
							<div className="flex items-center gap-3 mb-2">
								<div className="p-3 bg-primary/10 rounded-lg">
									<MessageSquare className="h-6 w-6 text-primary" />
								</div>
								<CardTitle className="text-2xl">Chat Rooms</CardTitle>
							</div>
							<CardDescription className="text-base">
								Join your conversations and catch up on messages
							</CardDescription>
						</CardHeader>
						<CardContent>
							<div className="space-y-3">
								<Button className="w-full" size="lg" onClick={() => navigate("/rooms")}>
									<MessageSquare className="mr-2 h-5 w-5" />
									View All Rooms
								</Button>
								<Button
									variant="outline"
									className="w-full"
									size="lg"
									onClick={(e) => {
										e.stopPropagation();
										navigate("/rooms/new");
									}}
								>
									<Plus className="mr-2 h-5 w-5" />
									Create New Room
								</Button>
							</div>
						</CardContent>
					</Card>

					{/* Contacts Card */}
					<Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate("/contacts")}>
						<CardHeader>
							<div className="flex items-center gap-3 mb-2">
								<div className="p-3 bg-primary/10 rounded-lg">
									<Users className="h-6 w-6 text-primary" />
								</div>
								<CardTitle className="text-2xl">Contacts</CardTitle>
							</div>
							<CardDescription className="text-base">
								Manage your contacts and start new conversations
							</CardDescription>
						</CardHeader>
						<CardContent>
							<div className="space-y-3">
								<Button className="w-full" size="lg" onClick={() => navigate("/contacts")}>
									<Users className="mr-2 h-5 w-5" />
									View Contacts
								</Button>
								<Button
									variant="outline"
									className="w-full"
									size="lg"
									onClick={(e) => {
										e.stopPropagation();
										navigate("/contacts");
									}}
								>
									<Search className="mr-2 h-5 w-5" />
									Find Friends
								</Button>
							</div>
						</CardContent>
					</Card>
				</div>

				{/* Quick Stats */}
				<div className="mt-12 max-w-4xl mx-auto">
					<div className="grid grid-cols-3 gap-4 text-center">
						<div className="p-4 bg-card rounded-lg">
							<div className="text-3xl font-bold text-primary mb-1">💬</div>
							<div className="text-sm text-muted-foreground">Active Chats</div>
						</div>
						<div className="p-4 bg-card rounded-lg">
							<div className="text-3xl font-bold text-primary mb-1">👥</div>
							<div className="text-sm text-muted-foreground">Contacts</div>
						</div>
						<div className="p-4 bg-card rounded-lg">
							<div className="text-3xl font-bold text-primary mb-1">⭐</div>
							<div className="text-sm text-muted-foreground">Favorites</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};
