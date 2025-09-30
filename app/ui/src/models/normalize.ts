/* eslint-disable @typescript-eslint/no-explicit-any */
import type { MessageDto, RoomDto, UserDto } from "./dto";
import type { RoomControlMessage, WebSocketEnvelope } from "./info";

function isString(v: any): v is string {
	return typeof v === "string";
}

export function normalizeMessageDto(raw: any): MessageDto | null {
	if (!raw || typeof raw !== "object") return null;

	try {
		const id = raw.id;
		const roomId = raw.room_id ?? raw.roomId;
		const senderId = raw.sender_id ?? raw.senderId;
		const content = raw.content;
		const messageType = raw.message_type ?? raw.messageType;
		const replyToId = raw.reply_to_id ?? raw.replyToId ?? null;
		const createdAt = raw.created_at ?? raw.createdAt;
		const updatedAt = raw.updated_at ?? raw.updatedAt ?? null;
		const deletedAt = raw.deleted_at ?? raw.deletedAt ?? null;
		if (![id, roomId, senderId, content, messageType, createdAt].every(isString)) return null;
		return {
			id: String(id),
			roomId: String(roomId),
			senderId: String(senderId),
			content: String(content),
			messageType: String(messageType),
			replyToId: replyToId ? String(replyToId) : null,
			createdAt: String(createdAt),
			updatedAt: updatedAt ? String(updatedAt) : null,
			deletedAt: deletedAt ? String(deletedAt) : null,
		};
	} catch (error) {
		console.error("Failed to normalize message:", error, raw);
		return null;
	}
}

export function normalizeUserDto(raw: any): UserDto | null {
	try {
		return {
			userId: raw.user_id || raw.userId || "",
			username: raw.username || "",
			firstName: raw.first_name || raw.firstName || "",
			lastName: raw.last_name || raw.lastName || "",
			avatarUrl: raw.avatar_url || raw.avatarUrl || null,
			bio: raw.bio || null,
			email: raw.email || "",
			phoneNumber: raw.phone_number || raw.phoneNumber || null,
			isOnline: raw.is_online ?? raw.isOnline ?? false,
			lastSeen: raw.last_seen || raw.lastSeen || new Date().toISOString(),

			// Contact-specific fields
			nickname: raw.nickname || raw.username || null, // fallback to username
			isFavorite: raw.is_favorite ?? raw.isFavorite ?? null,
			isBlocked: raw.is_blocked ?? raw.isBlocked ?? null,
			contactSince: raw.contact_since || raw.contactSince || null,
		};
	} catch (error) {
		console.error("Failed to normalize user:", error, raw);
		return null;
	}
}

export function normalizeEnvelope(raw: any): WebSocketEnvelope | null {
	if (!raw || typeof raw !== "object") return null;

	try {
		const type = raw.type ?? null;
		const data = raw.data ?? null;
		switch (type) {
			case "message": {
				// { type: "message", data: { id: <uuid>, room_id: <uuid>, ... } }
				const msg = normalizeMessageDto(data);
				return msg ? { type: "message", data: msg } : null;
			}

			case "control": {
				// { type: "control", data: { room_id: <uuid>, status: "added" } }
				const roomId = data?.room_id ?? data?.roomId;
				const status = data?.status;
				if (!isString(roomId)) return null;
				if (typeof status !== "string") return null;
				if (!["added", "removed", "promoted", "demoted"].includes(status)) return null;
				return { type: "control", data: { roomId: String(roomId), status: status as RoomControlMessage['status'] } };
			}

			case "send_response": {
				// { type: "send_response", data: { message: MessageDto | null } }
				const inner = data?.message ?? null;
				const normalizedMessage = inner ? normalizeMessageDto(inner) : null;
				// allow null (no message) and return shape { message: MessageDto | null }
				return { type: "send_response", data: { message: normalizedMessage } };
			}

			case "error": {
				// { type: "error", data: { error: str | null } }
				const err = data?.error ?? (isString(data) ? data : String(data ?? ""));
				return { type: "error", data: { error: isString(err) ? err : String(err ?? "") } };
			}

			default: {
				// try to detect a bare MessageDto payload (no envelope)
				// this shouldn't happen but I might forget
				const msg = normalizeMessageDto(raw);
				if (msg) return { type: "message", data: msg };
				return null;
			}
		}
	} catch (error) {
		console.error("Failed to normalize websocket message:", error, raw);
		return null;
	}
}

export function normalizeRoomDto(raw: any): RoomDto | null {
	if (!raw || typeof raw !== "object") return null;

	try {
		// Extract basic fields with snake_case to camelCase conversion
		const id = raw.id || "";
		const name = raw.name || null;
		const description = raw.description || null;
		const roomType = raw.room_type || raw.roomType || "group"; // Default to group
		const createdBy = raw.created_by || raw.createdBy || "";
		const createdAt = raw.created_at || raw.createdAt || new Date().toISOString();
		const updatedAt = raw.updated_at || raw.updatedAt || null;
		const unreadCount = Number(raw.unread_count ?? raw.unreadCount ?? 0);

		// Process participants array
		const participants = Array.isArray(raw.participants)
			? raw.participants.map((p: any) => ({
				userId: String(p.user_id || p.userId || ""),
				role: (p.role || "member") as "owner" | "admin" | "member"
			}))
			: [];

		return {
			id: String(id),
			name,
			description,
			participants,
			roomType: roomType as "direct" | "group" | "channel",
			createdBy: String(createdBy),
			createdAt: String(createdAt),
			updatedAt: updatedAt ? String(updatedAt) : null,
			unreadCount: isNaN(unreadCount) ? 0 : unreadCount
		};
	} catch (error) {
		console.error("Failed to normalize room:", error, raw);
		return null;
	}
}
