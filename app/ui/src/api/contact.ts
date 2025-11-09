import { getUserService } from "@/config";
import type { UserDto } from "@/models/dto";
import { normalizeUserDto } from "@/models/normalize";

export class ContactsAPI {
	private static baseUrl: string = `https://${getUserService()}/api/v1/contacts`; // NOTE: change to http for local testing

	private static getHeaders(token: string) {
		return {
			"Authorization": `Bearer ${token}`,
			"Content-Type": "application/json",
		};
	}

	static async getContacts(token: string): Promise<UserDto[]> {
		const res = await fetch(`${this.baseUrl}`, {
			method: "GET",
			headers: this.getHeaders(token),
		});
		if (!res.ok) throw new Error("Failed to fetch contacts");
		const data = await res.json();
		return Array.isArray(data) ? data.map(normalizeUserDto).filter((u): u is UserDto => u !== null) : [];
	}

	static async addContact(token: string, contactUsername: string): Promise<UserDto> {
		const res = await fetch(`${this.baseUrl}`, {
			method: "POST",
			headers: this.getHeaders(token),
			body: JSON.stringify({ username: contactUsername }),
		});
		if (!res.ok) throw new Error("Failed to add contact");
		const data = await res.json();
		const user = normalizeUserDto(data);
		if (!user) throw new Error("Unexpected add contact response")
		return user;
	}

	static async deleteContact(token: string, contactId: string): Promise<void> {
		const res = await fetch(`${this.baseUrl}/${contactId}`, {
			method: "DELETE",
			headers: this.getHeaders(token),
		});
		if (!res.ok) throw new Error("Failed to delete contact");
	}

	static async updateContact(
		token: string,
		contactId: string,
		nickname?: string
	): Promise<UserDto> {
		const res = await fetch(`${this.baseUrl}/${contactId}`, {
			method: "PUT",
			headers: this.getHeaders(token),
			body: JSON.stringify({ nickname }),
		});
		if (!res.ok) throw new Error("Failed to update contact");

		const data = await res.json();
		const user = normalizeUserDto(data);
		if (!user) throw new Error("Unexpected update contact response")
		return user;
	}

	static async getFavorites(token: string): Promise<UserDto[]> {
		const res = await fetch(`${this.baseUrl}/favorites`, {
			method: "GET",
			headers: this.getHeaders(token),
		});

		if (!res.ok) throw new Error("Failed to fetch favorites");
		const data = await res.json();
		return Array.isArray(data) ? data.map(normalizeUserDto).filter((u): u is UserDto => u !== null) : [];
	}

	static async toggleFavorite(token: string, contactId: string): Promise<UserDto> {
		const res = await fetch(`${this.baseUrl}/${contactId}/favorite`, {
			method: "POST",
			headers: this.getHeaders(token),
		});
		if (!res.ok) throw new Error("Failed to toggle favorite");

		const data = await res.json();
		const user = normalizeUserDto(data);
		if (!user) throw new Error("Unexpected toggle favorite response")
		return user;
	}

	static async getBlocked(token: string): Promise<UserDto[]> {
		const res = await fetch(`${this.baseUrl}/blocked`, {
			method: "GET",
			headers: this.getHeaders(token),
		});
		if (!res.ok) throw new Error("Failed to fetch blocked contacts");
		const data = await res.json();
		return Array.isArray(data) ? data.map(normalizeUserDto).filter((u): u is UserDto => u !== null) : [];
	}

	static async toggleBlockUser(token: string, contactId: string): Promise<void> {
		const res = await fetch(`${this.baseUrl}/${contactId}/block`, {
			method: "POST",
			headers: this.getHeaders(token),
		});
		if (!res.ok) throw new Error("Failed to toggle blocked user");
	}
}
