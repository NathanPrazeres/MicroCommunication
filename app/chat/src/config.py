from os import environ as env

PG_NAME = env.get("PG_NAME")
PG_USER = env.get("PG_USER")
PG_PASS = env.get("PG_PASS")
JWT_PUB_KEY = env.get("JWT_PUBLIC_KEY")
JWT_ALG = "RS256"
