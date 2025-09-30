from uuid import UUID
from psycopg_pool import AsyncConnectionPool
from typing import Optional
import config
from models.dto import MessageDto, RoomDto, RoomParticipantDto
from utils.user_info import get_user_info
import logging

logger = logging.getLogger(__name__)


class PostgresClient:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None

    async def open(self):
        """Open the pool when FastAPI starts"""
        logger.info("Opening PostgreSQL connection pool")
        self.pool = AsyncConnectionPool(
            f"host={config.PG_HOST} port={config.PG_PORT} dbname={config.PG_NAME} user={config.PG_USER} password={config.PG_PASS}",
            min_size=1,
            max_size=10,
            max_idle=300, # idle timeout in seconds
            open=False
        )
        await self.pool.open(wait=True)
        logger.info("PostgreSQL connection pool opened successfully")

    async def close(self):
        """Close the pool when FastAPI shuts down"""
        if not self.pool:
            logger.warning("Attempted to close PostgreSQL pool that was never opened")
            return
        logger.info("Closing PostgreSQL connection pool")
        await self.pool.close()
        logger.info("PostgreSQL connection pool closed")

    async def get_room_users(self, room_id: UUID) -> list[UUID]:
        """
        Fetches users in a room and returns their user IDs.
        """
        logger.debug("Fetching users for room: %s", str(room_id))
        if not self.pool:
            await self.open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT user_id FROM room_participants WHERE room_id = %s",
                    (room_id,)
                )
                users = await curr.fetchall()
        user_ids = [u[0] for u in users]
        logger.debug("Found %d users in room %s", len(user_ids), str(room_id))
        return user_ids

    async def create_room(
        self,
        name: Optional[str],
        room_type: str,
        created_by: UUID,
        participants: list[UUID],
        description: Optional[str] = None
    ) -> UUID:
        """
        Creates a chat room with participants and returns the room ID.
        The creator is automatically added as 'owner'.
        For direct rooms, check if the room already exists and return it's UUID if so.
        """
        logger.info("Creating room '%s' (type: %s) by user: %s", name, room_type, str(created_by))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                # If the room is a direct connection return the existing one if it exists
                if room_type == "direct" and len(participants) == 1:
                    other_user = participants[0]
                    await curr.execute(
                        """
                        SELECT r.id
                        FROM rooms r
                        WHERE r.room_type = 'direct'
                        AND EXISTS (
                            SELECT 1 FROM room_participants rp1
                            WHERE rp1.room_id = r.id AND rp1.user_id = %s
                        )
                        AND EXISTS (
                            SELECT 1 FROM room_participants rp2
                            WHERE rp2.room_id = r.id AND rp2.user_id = %s
                        )
                        AND (
                            SELECT COUNT(*) FROM room_participants
                            WHERE room_id = r.id
                        ) = 2
                        LIMIT 1
                        """,
                        (created_by, other_user)
                    )
                    existing_room = await curr.fetchone()
                    if existing_room:
                        room_id = existing_room[0]
                        logger.info("Found existing direct room: %s", str(room_id))
                        return room_id

                # Insert the room
                await curr.execute(
                    """
                    INSERT INTO rooms (name, description, room_type, created_by)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, description, room_type, created_by)
                )
                room_id = (await curr.fetchone())[0]
                logger.info("Room created with ID: %s", str(room_id))

                # Insert creator as owner
                await curr.execute(
                    """
                    INSERT INTO room_participants (room_id, user_id, role)
                    VALUES (%s, %s, 'owner')
                    """,
                    (room_id, created_by)
                )

                # Insert other participants as members
                added_count = 0
                for user_id in participants:
                    if user_id == created_by or not await get_user_info(user_id):
                        logger.debug("Skipping invalid/duplicate user: %s", str(user_id))
                        continue # Ignore invalid users
                    await curr.execute(
                        """
                        INSERT INTO room_participants (room_id, user_id, role)
                        VALUES (%s, %s, 'member')
                        """,
                        (room_id, user_id)
                    )
                    added_count += 1
                logger.info("Added %d participants to room %s", added_count, str(room_id))

        return room_id

    async def get_room_messages(self, user_id: UUID, room_id: UUID) -> Optional[list[MessageDto]]:
        """
        Returns a list of all past messages from a room.

        Returns None if the user isn't in the room.
        """
        logger.debug("Fetching messages for room %s by user %s", str(room_id), str(user_id))
        if not await self.is_user_in_room(user_id, room_id):
            logger.warning("User %s not in room %s, denying message access", str(user_id), str(room_id))
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    SELECT id, room_id, sender_id, content, message_type, reply_to_id, created_at, updated_at, deleted_at
                    FROM messages
                    WHERE room_id = %s
                    ORDER BY created_at ASC
                    """,
                    (room_id,)
                )
                rows = await curr.fetchall()

        messages = [
            MessageDto(
                id=row[0],
                room_id=row[1],
                sender_id=row[2],
                content=row[3],
                message_type=row[4],
                reply_to_id=row[5],
                created_at=row[6],
                updated_at=row[7],
                deleted_at=row[8],
            )
            for row in rows
        ]
        logger.debug("Retrieved %d messages from room %s", len(messages), str(room_id))
        return messages

    async def send_message(self, user_id: UUID, room_id: UUID, content: str, reply_to_id: Optional[UUID] = None) -> Optional[MessageDto]:
        """
        Creates a message entry in the database and returns the message.

        Returns None when the message can't be sent.
        """
        logger.debug("User %s sending message to room %s", str(user_id), str(room_id))
        if not await self.is_user_in_room(user_id, room_id):
            logger.warning("User %s not in room %s, message denied", str(user_id), str(room_id))
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    INSERT INTO messages (room_id, sender_id, content, reply_to_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, room_id, sender_id, content, message_type, reply_to_id, created_at, updated_at, deleted_at
                    """,
                    (room_id, user_id, content, reply_to_id)
                )
                msg = await curr.fetchone()
                if msg is None:
                    logger.error("Failed to insert message for user %s in room %s", str(user_id), str(room_id))
                    return None
                message = MessageDto(
                    id=msg[0],
                    room_id=msg[1],
                    sender_id=msg[2],
                    content=msg[3],
                    message_type=msg[4],
                    reply_to_id=msg[5],
                    created_at=msg[6],
                    updated_at=msg[7],
                    deleted_at=msg[8],
                )
                logger.info("Message %s created in room %s by user %s", str(message.id), str(room_id), str(user_id))
                return message

    async def is_user_in_room(self, user_id: UUID, room_id: UUID) -> bool:
        """
        Checks whether a user is in a given room.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    SELECT 1
                    FROM room_participants
                    WHERE room_id = %s AND user_id = %s
                    LIMIT 1
                    """,
                    (room_id, user_id)
                )
                result = (await curr.fetchone()) is not None
                logger.debug("User %s in room %s: %s", str(user_id), str(room_id), result)
                return result

    async def add_room_user(self, user_id: UUID, room_id: UUID) -> None:
        """
        Add a user to the room.
        """
        logger.info("Adding user %s to room %s", str(user_id), str(room_id))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "INSERT INTO room_participants (room_id, user_id) VALUES (%s, %s)",
                    (room_id, user_id)
                )

    async def remove_room_user(self, user_id: UUID, room_id: UUID) -> None:
        """
        Remove a user from the room.
        """
        logger.info("Removing user %s from room %s", str(user_id), str(room_id))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "DELETE FROM room_participants WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )

    async def promote_room_user(self, user_id: UUID, room_id: UUID) -> None:
        """
        Promote a user to admin in the room.
        """
        logger.info("Promoting user %s to admin in room %s", str(user_id), str(room_id))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "UPDATE room_participants SET role = 'admin' WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )

    async def demote_room_user(self, user_id: UUID, room_id: UUID) -> None:
        """
        Demote a user from admin to member in the room.
        """
        logger.info("Demoting user %s to member in room %s", str(user_id), str(room_id))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "UPDATE room_participants SET role = 'member' WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )

    async def is_user_admin(self, user_id: UUID, room_id: UUID, owner_only: bool = False) -> bool:
        """
        Checks whether a user is an admin (or owner) in a given room.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                if owner_only:
                    await curr.execute(
                        """
                        SELECT 1
                        FROM room_participants
                        WHERE room_id = %s AND user_id = %s AND role = 'owner'
                        LIMIT 1
                        """,
                        (room_id, user_id)
                    )
                else:
                    await curr.execute(
                        """
                        SELECT 1
                        FROM room_participants
                        WHERE room_id = %s AND user_id = %s AND (role = 'admin' OR role = 'owner')
                        LIMIT 1
                        """,
                        (room_id, user_id)
                    )
                result = (await curr.fetchone()) is not None
                logger.debug("User %s is admin in room %s (owner_only=%s): %s", str(user_id), str(room_id), owner_only, result)
                return result

    async def get_user_rooms(self, user_id: UUID) -> list[RoomDto]:
        """
        Get all room info for rooms the user is a participant in.
        """
        logger.debug("Fetching rooms for user: %s", str(user_id))
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    SELECT r.id, r.name, r.description, r.room_type, r.created_by, r.created_at, r.updated_at,
                           (SELECT COUNT(*) FROM messages
                            WHERE room_id = r.id AND NOT sender_id = rp.user_id
                            AND (rp.last_read_at IS NULL OR created_at > rp.last_read_at)) as unread_count
                    FROM rooms r
                    JOIN room_participants rp ON r.id = rp.room_id
                    WHERE rp.user_id = %s
                    """,
                    (user_id,)
                )
                rows = await curr.fetchall()

                # Fetch participants for each room
                rooms = []
                for row in rows:
                    room_id = row[0]
                    await curr.execute(
                        """
                        SELECT user_id, role
                        FROM room_participants
                        WHERE room_id = %s
                        """,
                        (room_id,)
                    )
                    participant_rows = await curr.fetchall()
                    participants = [
                        RoomParticipantDto(user_id=p[0], role=p[1])
                        for p in participant_rows
                    ]

                    rooms.append(RoomDto(
                        id=room_id,
                        name=row[1],
                        description=row[2],
                        room_type=row[3],
                        created_by=row[4],
                        created_at=row[5],
                        updated_at=row[6],
                        unread_count=row[7],
                        participants=participants,
                    ))

        logger.debug("User %s has %d rooms", str(user_id), len(rooms))
        return rooms

    async def get_room_info(self, user_id: UUID, room_id: UUID) -> Optional[RoomDto]:
        """
        Get room info for a specific room the user is a participant in.
        Returns None if the user is not in the room.
        """
        logger.debug("Fetching room info for room %s by user %s", str(room_id), str(user_id))
        if not await self.is_user_in_room(user_id, room_id):
            logger.warning("User %s not in room %s, denying room info access", str(user_id), str(room_id))
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    SELECT r.id, r.name, r.description, r.room_type, r.created_by, r.created_at, r.updated_at,
                           (SELECT COUNT(*) FROM messages
                            WHERE room_id = r.id AND NOT sender_id = rp.user_id
                            AND (rp.last_read_at IS NULL OR created_at > rp.last_read_at)) as unread_count
                    FROM rooms r
                    JOIN room_participants rp ON r.id = rp.room_id
                    WHERE rp.user_id = %s AND r.id = %s
                    """,
                    (user_id, room_id)
                )
                row = await curr.fetchone()

                if row is None:
                    logger.warning("Room info not found for room %s and user %s", str(room_id), str(user_id))
                    return None

                # Fetch participants
                await curr.execute(
                    """
                    SELECT user_id, role
                    FROM room_participants
                    WHERE room_id = %s
                    """,
                    (room_id,)
                )
                participant_rows = await curr.fetchall()
                participants = [
                    RoomParticipantDto(user_id=p[0], role=p[1])
                    for p in participant_rows
                ]

        return RoomDto(
            id=row[0],
            name=row[1],
            description=row[2],
            room_type=row[3],
            created_by=row[4],
            created_at=row[5],
            updated_at=row[6],
            unread_count=row[7],
            participants=participants,
        )

    async def mark_as_read(self, user_id: UUID, room_id: UUID) -> None:
        """
        Updates the last_read_at timestamp.
        """
        logger.debug("Marking room %s as read for user %s", str(room_id), str(user_id))
        if not await self.is_user_in_room(user_id, room_id):
            logger.warning("User %s not in room %s, cannot mark as read", str(user_id), str(room_id))
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """
                    UPDATE room_participants
                    SET last_read_at = NOW()
                    WHERE room_id = %s AND user_id = %s
                    """,
                    (room_id, user_id)
                )
        logger.info("Room %s marked as read for user %s", str(room_id), str(user_id))

    async def delete_room(self, user_id: UUID, room_id: UUID) -> bool:
        """
        Deletes a room if the user is the owner.
        Returns True if the room was deleted, False if the user doesn't have permission.
        """
        logger.info("Attempting to delete room %s by user %s", str(room_id), str(user_id))

        # Check if user is the owner
        if not await self.is_user_admin(user_id, room_id, owner_only=True):
            logger.warning("User %s is not the owner of room %s, cannot delete", str(user_id), str(room_id))
            return False

        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                # Delete all messages in the room first (due to foreign key constraints)
                await curr.execute(
                    "DELETE FROM messages WHERE room_id = %s",
                    (room_id,)
                )
                messages_deleted = curr.rowcount
                logger.debug("Deleted %d messages from room %s", messages_deleted, str(room_id))

                # Delete all room participants
                await curr.execute(
                    "DELETE FROM room_participants WHERE room_id = %s",
                    (room_id,)
                )
                participants_deleted = curr.rowcount
                logger.debug("Deleted %d participants from room %s", participants_deleted, str(room_id))

                # Delete the room itself
                await curr.execute(
                    "DELETE FROM rooms WHERE id = %s",
                    (room_id,)
                )

                logger.info("Successfully deleted room %s", str(room_id))
                return True

postgres_client = PostgresClient()
