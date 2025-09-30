import type { MessageDto } from "./dto";

export type UnreadMap = {
  [roomId: string]: number
}

export type RoomControlMessage = {
  roomId: string;
  status: "added" | "removed" | "promoted" | "demoted";
};

export type SendMessageResponse = {
  message?: MessageDto | null;
};

export type ErrorMessage = {
  error?: string | null;
};

export type WebSocketEnvelope =
  | { type: "message"; data: MessageDto }
  | { type: "control"; data: RoomControlMessage }
  | { type: "send_response"; data: SendMessageResponse }
  | { type: "error"; data: ErrorMessage };
