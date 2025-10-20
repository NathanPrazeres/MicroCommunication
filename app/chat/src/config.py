from os import environ as env

PG_HOST = env.get("PG_HOST", "localhost")
PG_PORT = env.get("PG_PORT", "5432")
PG_NAME = env.get("PG_NAME")
PG_USER = env.get("PG_USER")
PG_PASS = env.get("PG_PASS")

REDIS_HOST = env.get("REDIS_HOST", "localhost")
REDIS_PORT = env.get("REDIS_PORT", "6379")

USER_HOST = env.get("USER_HOST", "localhost")
USER_PORT = env.get("USER_PORT")
USER_SERVICE = env.get("USER_SERVICE", f"{USER_HOST}:{USER_PORT}")

FRONTEND_HOST = env.get("FRONTEND_HOST", "localhost")
FRONTEND_PORT = env.get("FRONTEND_PORT", "4173")
FRONTEND_SERVICE = env.get("FRONTEND_SERVICE", f"{FRONTEND_HOST}:{FRONTEND_PORT}")

AUTH_HOST = env.get("AUTH_HOST", "localhost")
AUTH_PORT = env.get("AUTH_PORT", "8080")
AUTH_SERVICE = env.get("AUTH_SERVICE", f"{AUTH_HOST}:{AUTH_PORT}")
AUTH_REALM = env.get("AUTH_REALM")

JWT_ALG = "RS256"
