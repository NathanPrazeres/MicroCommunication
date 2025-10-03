import psycopg
from os import environ as env

PG_NAME = env.get("PG_NAME")
PG_USER = env.get("PG_USER")
PG_PASS = env.get("PG_PASS")

def get_room_users(room_id: int):
    users = []
    with psycopg.connect(f"host='db.local' port='5432' dbname='{PG_NAME}' user='{PG_USER}' password='{PG_PASS}'") as conn:
        with conn.cursor() as curr:
            curr.execute("""SELECT user_id FROM ROOM_PARTICIPANTS WHERE room_id=%s""", (room_id,))
            users = curr.fetchmany()

    return users
