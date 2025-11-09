import { getUserService } from "@/config";
import type { UserDto } from "@/models/dto";
import { normalizeUserDto } from "@/models/normalize";

export class UsersAPI {
  private static baseUrl: string = `https://${getUserService()}/api/v1/users`; // NOTE: change to http for local testing

  private static getHeaders(token: string) {
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  // Create user profile (called on first login)
  static async createUser(
    token: string,
    bio?: string,
    avatarUrl?: string,
    phoneNumber?: string
  ): Promise<UserDto> {
    const res = await fetch(`${this.baseUrl}`, {
      method: "POST",
      headers: this.getHeaders(token),
      body: JSON.stringify({
        bio,
        avatar_url: avatarUrl,
        phone_number: phoneNumber,
      }),
    });
    if (!res.ok) throw new Error("Failed to create user");
    return await res.json();
  }

  // Get another user's profile (must be in contacts)
  static async getUser(token: string, userId: string): Promise<UserDto> {
    const res = await fetch(`${this.baseUrl}/${userId}`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) {
      if (res.status === 403) {
        throw new Error("User is not in your contacts");
      }
      throw new Error("Failed to fetch user");
    }

    const user = normalizeUserDto(await res.json());
    if (!user) throw new Error("Unexpected get user response");
    return user;
  }

  // Get current user's own profile
  static async getCurrentUser(token: string): Promise<UserDto> {
    const res = await fetch(`${this.baseUrl}/@me`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to fetch current user");

    const user = normalizeUserDto(await res.json());
    if (!user) throw new Error("Unexpected get user response");
    return user;
  }

  // Update current user's profile
  static async updateUser(
    token: string,
    bio?: string,
    avatarUrl?: string
  ): Promise<UserDto> {
    const res = await fetch(`${this.baseUrl}/@me`, {
      method: "PUT",
      headers: this.getHeaders(token),
      body: JSON.stringify({
        bio: bio || null,
        avatar_url: avatarUrl || null,
      }),
    });
    if (!res.ok) throw new Error("Failed to update user");

    const user = normalizeUserDto(await res.json());
    if (!user) throw new Error("Unexpected get user response");
    return user;
  }

  // Delete current user's account
  static async deleteUser(token: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/@me`, {
      method: "DELETE",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to delete user");
  }
}