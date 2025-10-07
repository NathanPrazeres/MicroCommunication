from uuid import UUID
from psycopg_pool import AsyncConnectionPool
from typing import Optional
import config
from models.dto import MessageDto, UserDto


class PostgresClient:
    def __init__(self):
        # TODO: make sure the conninfo and host is correct
        self.pool = AsyncConnectionPool(
            f"host=db.local port=5432 dbname={config.PG_NAME} user={config.PG_USER} password={config.PG_PASS}",
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
                users = await curr.fetchall()

        user_list: list[UserDto] = []
        for user in users:
            user_list.append(UserDto(id=user[0], username=user[1]))

        return user_list

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
        if not await self.user_in_room(user_id, room_id):
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

    async def user_in_room(self, user_id: UUID, room_id: UUID) -> bool:
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

    async def add_user_room(self, user_id: UUID, room_id: UUID) -> None:
        """
        Add a user to the room.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "INSERT INTO room_participants (room_id, user_id) VALUES (%s, %s)",
                    (room_id, user_id)
                )

    async def is_user_admin(self, user_id: UUID, room_id: UUID) -> bool:
        """
        Checks whether a user is an admin (or owner) in a given room.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
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

    async def get_user_rooms(self, user_id: UUID) -> list[UUID]:
        """
        Get a list of rooms a given user belongs to.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    "SELECT room_id FROM room_participants WHERE user_id = %s",
                    (user_id,)
                )
                rooms = await curr.fetchall()
                if rooms is None:
                    return []
                return [r[0] for r in rooms]


postgres_client = PostgresClient()
