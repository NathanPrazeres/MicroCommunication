from uuid import UUID
from psycopg_pool import AsyncConnectionPool
from typing import Optional
import config
from models.dto import MessageDto, UserDto, RoomDto


class PostgresClient:
    def __init__(self):
        # TODO: make sure the conninfo and host is correct
        self.pool = AsyncConnectionPool(
            f"host={config.PG_HOST} port={config.PG_PORT} dbname={config.PG_NAME} user={config.PG_USER} password={config.PG_PASS}",
            min_size=1,
            max_size=10,
            max_idle=300 # idle timeout in seconds
        )

    async def open(self):
        """Open the pool when FastAPI starts"""
        await self.pool.open(wait=True)

    async def close(self):
        """Close the pool when FastAPI shuts down"""
        await self.pool.close()

    async def is_valid_user(self, user_id: UUID) -> bool:
        """
        Checks whether a user_id exists in the users table.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT 1 FROM users WHERE id = %s LIMIT 1",
                    (user_id,)
                )
                return (await curr.fetchone()) is not None

    async def get_room_users(self, room_id: UUID) -> list[UUID]:
        """
        Fetches users in a room and returns their user IDs.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT user_id FROM room_participants WHERE room_id = %s",
                    (room_id,)
                )
                users = await curr.fetchall()
        return [u[0] for u in users]

    async def get_contacts(self, user_id: UUID) -> list[UserDto]:
        """
        Fetches contacts of a user and returns their user IDs and names.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT contact_id, nickname FROM contacts WHERE user_id = %s",
                    (user_id,)
                )
                rows = await curr.fetchall()

        return [
            UserDto(id=row[0], username=row[1])
            for row in rows
        ]

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
                    if user_id == created_by:
                        continue
                    await curr.execute(
                        """
                        INSERT INTO room_participants (room_id, user_id, role)
                        VALUES (%s, %s, 'member')
                        """,
                        (room_id, user_id)
                    )

        return room_id

    async def send_message(self, user_id: UUID, room_id: UUID, content: str) -> Optional[MessageDto]:
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
                    INSERT INTO messages (room_id, sender_id, content)
                    VALUES (%s, %s, %s)
                    RETURNING (id, room_id, sender_id, content, message_type, reply_to_id, created_at, updated_at, deleted_at)
                    """,
                    (room_id, user_id, content)
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
        if not self.is_valid_user(user_id):
            return None

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
                    SELECT r.id, r.name, r.description, r.room_type, r.created_by, r.created_at, r.updated_at
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
            )
            for row in rows
        ]

postgres_client = PostgresClient()
