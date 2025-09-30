import { getChatService } from "@/config";
import type { RoomDto, MessageDto, RoomUserDto } from "@/models/dto";
import { normalizeMessageDto, normalizeRoomDto } from "@/models/normalize";

export class RoomsAPI {
  private static baseUrl: string = `http://${getChatService()}/api/v1/rooms`;

  private static getHeaders(token: string) {
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  // Get all rooms for the current user
  static async getRooms(token: string): Promise<RoomDto[]> {
    const res = await fetch(`${this.baseUrl}`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to fetch rooms");
    const data = await res.json();

    const rooms = (data.rooms || [])
      .map((room: object) => normalizeRoomDto(room))
      .filter((room: object): room is RoomDto => room !== null);
    return rooms || [];
  }

  // Get a specific room by ID
  static async getRoom(token: string, roomId: string): Promise<RoomDto> {
    const res = await fetch(`${this.baseUrl}/${roomId}`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to fetch room");
    const data = await res.json();
    const room = normalizeRoomDto(data.room);
    if (!room) throw new Error("Unexpected fetch room response");
    return room;
  }

  // Create a new room
  static async createRoom(
    token: string,
    roomType: "direct" | "group" | "channel",
    participants: string[] = [],
    name: string | null = null,
    description: string | null = null
  ): Promise<string> {
    const res = await fetch(`${this.baseUrl}`, {
      method: "POST",
      headers: this.getHeaders(token),
      body: JSON.stringify({
        name,
        description,
        room_type: roomType,
        participants: participants,
      }),
    });
    if (!res.ok) throw new Error("Failed to create room");
    const data = await res.json();
    return data.room_id;
  }

  // Get messages for a room
  static async getMessages(token: string, roomId: string): Promise<MessageDto[]> {
    const res = await fetch(`${this.baseUrl}/${roomId}/messages`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to fetch messages");
    const data = await res.json();
    const normalizedMessages = (data.messages || [])
      .map((msg: object) => normalizeMessageDto(msg))
      .filter((msg: object): msg is MessageDto => msg !== null);
    return normalizedMessages || [];
  }

  // Send a message to a room (HTTP fallback, WebSocket preferred)
  static async sendMessage(
    token: string,
    roomId: string,
    content: string,
    replyToId?: string
  ): Promise<MessageDto | null> {
    const res = await fetch(`${this.baseUrl}/${roomId}/messages`, {
      method: "POST",
      headers: this.getHeaders(token),
      body: JSON.stringify({
        room_id: roomId,
        content,
        reply_to_id: replyToId,
      }),
    });
    if (!res.ok) throw new Error("Failed to send message");
    const data = await res.json();
    return normalizeMessageDto(data.message) || null;
  }

  // Mark all messages in a room as read
  static async markAsRead(token: string, roomId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/${roomId}/messages`, {
      method: "PATCH",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to mark as read");
    const data = await res.json();
    return data.message;
  }

  // Get room members/users
  static async getUsers(token: string, roomId: string): Promise<RoomUserDto[]> {
    const res = await fetch(`${this.baseUrl}/${roomId}/users`, {
      method: "GET",
      headers: this.getHeaders(token),
    });
    if (!res.ok) throw new Error("Failed to fetch users");
    const data = await res.json();
    // This one doesn't need normalization
    return data.users || [];
  }

  // Add a user to a room (admin only)
  static async addUser(token: string, roomId: string, userId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/${roomId}/users`, {
      method: "PUT",
      headers: this.getHeaders(token),
      body: JSON.stringify({ user_id: userId }),
    });
    if (!res.ok) throw new Error("Failed to add user");
    const data = await res.json();
    return data.message;
  }

  // Remove a user from a room (admin only)
  static async removeUser(token: string, roomId: string, userId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/${roomId}/users`, {
      method: "DELETE",
      headers: this.getHeaders(token),
      body: JSON.stringify({ user_id: userId }),
    });
    if (!res.ok) throw new Error("Failed to remove user");
    const data = await res.json();
    return data.message;
  }

  // Promote or demote a user (admin only)
  static async updateUserRole(
    token: string,
    roomId: string,
    userId: string,
    role: "member" | "admin"
  ): Promise<string> {
    const res = await fetch(`${this.baseUrl}/${roomId}/users`, {
      method: "PATCH",
      headers: this.getHeaders(token),
      body: JSON.stringify({ user_id: userId, role }),
    });
    if (!res.ok) throw new Error("Failed to update user role");
    const data = await res.json();
    return data.message;
  }
}