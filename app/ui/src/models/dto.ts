export interface RoomParticipantDto {
  userId: string;
  role: "owner" | "admin" | "member";
}

export interface RoomDto {
  id: string;
  name: string | null;
  description: string | null;
  participants: RoomParticipantDto[];
  roomType: "direct" | "group" | "channel";
  createdBy: string;
  createdAt: string; // ISO datetime
  updatedAt: string | null; // ISO datetime
  unreadCount: number;
}

export interface UserDto {
  userId: string;
  username: string;
  firstName: string;
  lastName: string;
  avatarUrl: string | null;
  bio: string | null;
  email: string;
  phoneNumber: string | null;
  isOnline: boolean;
  lastSeen: string; // ISO datetime

  // Contact-specific fields (only present when fetched through contacts API)
  nickname: string | null;
  isFavorite: boolean | null;
  isBlocked: boolean | null;
  contactSince: string | null; // ISO datetime
}

// Simplified user info returned by rooms API
export interface RoomUserDto {
  id: string;
  name: string;
  email: string;
}

export interface MessageDto {
  id: string;
  roomId: string;
  senderId: string;
  content: string;
  messageType: string;
  replyToId: string | null;
  createdAt: string; // ISO datetime
  updatedAt: string | null; // ISO datetime
  deletedAt: string | null; // ISO datetime
}