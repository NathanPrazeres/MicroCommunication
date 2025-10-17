from os import environ as env

PG_HOST = env.get("PG_HOST")
PG_NAME = env.get("PG_NAME")
PG_USER = env.get("PG_USER")
PG_PASS = env.get("PG_PASS")
USER_SERVICE = env.get("USER_SERVICE")
USER_PORT = env.get("USER_PORT")
AUTH_SERVICE = env.get("AUTH_SERVICE")
AUTH_PORT = env.get("AUTH_PORT")
AUTH_REALM = env.get("AUTH_REALM")
JWT_ALG = "RS256"
