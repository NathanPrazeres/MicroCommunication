import config
import httpx
import jwt
import asyncio


class JwtManager():
    def __init__(self):
        self.jwks_client = None
        self.issuer = None

    async def refresh_keys(self):
        url = f"http://{config.AUTH_SERVICE}:{config.AUTH_PORT}/realms/{config.AUTH_REALM}/.well-known/openid-configuration"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            self.issuer = resp.json()["issuer"]
            jwks_uri = resp.json()["jwks_uri"]

            self.jwks_client = jwt.PyJWKClient(jwks_uri)

    async def decode_token(self, token: str):
        if self.jwks_client is None or self.issuer is None:
            await self.refresh_keys()

        signing_key = await asyncio.to_thread(self.jwks_client.get_signing_key_from_jwt, token)

        return await asyncio.to_thread(
            jwt.decode,
            jwt=token,
            key=signing_key.key,
            algorithms=[config.JWT_ALG],
            issuer=self.issuer,
            options={"verify_signature": True, "require": ["sub"]}, # require the subject claim to be present
        )

jwt_manager = JwtManager()
