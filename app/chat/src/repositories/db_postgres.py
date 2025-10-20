from uuid import UUID
from psycopg_pool import AsyncConnectionPool
from typing import Optional
import config
from models.dto import MessageDto, RoomDto
from utils.user_info import get_user_info


class PostgresClient:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None

    async def open(self):
        """Open the pool when FastAPI starts"""
        self.pool = AsyncConnectionPool(
            f"host={config.PG_HOST} port={config.PG_PORT} dbname={config.PG_NAME} user={config.PG_USER} password={config.PG_PASS}",
            min_size=1,
            max_size=10,
            max_idle=300, # idle timeout in seconds
            open=False
        )
        await self.pool.open(wait=True)

    async def close(self):
        """Close the pool when FastAPI shuts down"""
        if not self.pool:
            return
        await self.pool.close()

    async def get_room_users(self, room_id: UUID) -> list[UUID]:
        """
        Fetches users in a room and returns their user IDs.
        """
        if not self.pool:
            await self.open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT user_id FROM room_participants WHERE room_id = %s",
                    (room_id,)
                )
                users = await curr.fetchall()
        return [u[0] for u in users]

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
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
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

                # Insert creator as owner
                await curr.execute(
                    """
                    INSERT INTO room_participants (room_id, user_id, role)
                    VALUES (%s, %s, 'owner')
                    """,
                    (room_id, created_by)
                )

                # Insert other participants as members
                for user_id in participants:
                    if user_id == created_by or not await get_user_info(user_id):
                        continue # Ignore invalid users
                    await curr.execute(
                        """
                        INSERT INTO room_participants (room_id, user_id, role)
                        VALUES (%s, %s, 'member')
                        """,
                        (room_id, user_id)
                    )

        return room_id

    async def get_room_messages(self, user_id: UUID, room_id: UUID) -> Optional[list[MessageDto]]:
        """
        Returns a list of all past messages from a room.

        Returns None if the user isn't in the room.
        """
        if not await self.is_user_in_room(user_id, room_id):
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

        return [
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

    async def send_message(self, user_id: UUID, room_id: UUID, content: str, reply_to_id: Optional[UUID] = None) -> Optional[MessageDto]:
        """
        Creates a message entry in the database and returns the message.

        Returns None when the message can't be sent.
        """
        if not await self.is_user_in_room(user_id, room_id):
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
                    return None
                return MessageDto(
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
                return (await curr.fetchone()) is not None

    async def add_room_user(self, user_id: UUID, room_id: UUID) -> None:
        """
        Add a user to the room.
        """
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
                return (await curr.fetchone()) is not None

    async def get_user_rooms(self, user_id: UUID) -> list[RoomDto]:
        """
        Get all room info for rooms the user is a participant in.
        """
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
        return [
            RoomDto(
                id=row[0],
                name=row[1],
                description=row[2],
                room_type=row[3],
                created_by=row[4],
                created_at=row[5],
                updated_at=row[6],
                unread_count=row[7],
            )
            for row in rows
        ]
    async def get_room_info(self, user_id: UUID, room_id: UUID) -> Optional[RoomDto]:
        """
        Get room info for a specific room the user is a participant in.
        Returns None if the user is not in the room.
        """
        if not await self.is_user_in_room(user_id, room_id):
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
            return None

        return RoomDto(
            id=row[0],
            name=row[1],
            description=row[2],
            room_type=row[3],
            created_by=row[4],
            created_at=row[5],
            updated_at=row[6],
            unread_count=row[7],
        )

    async def mark_as_read(self, user_id: UUID, room_id: UUID) -> None:
        """
        Updates the last_read_at timestamp.
        """
        if not await self.is_user_in_room(user_id, room_id):
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

postgres_client = PostgresClient()
