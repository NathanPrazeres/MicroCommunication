import config
import httpx
import jwt
import asyncio
import logging

logger = logging.getLogger(__name__)


class JwtManager():
    def __init__(self):
        self.jwks_client = None
        self.issuer = None
        self.external_issuer = None

    async def refresh_keys(self):
        logger.info("Refreshing Keycloak JWKs")
        url = f"http://{config.AUTH_SERVICE}/realms/{config.AUTH_REALM}/.well-known/openid-configuration"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

            self.issuer = resp.json()["issuer"]
            # TODO: should probably remove this in finished version but needs to be here in testing
            self.external_issuer = f"http://localhost:{config.AUTH_PORT}/realms/{config.AUTH_REALM}"

            jwks_uri = resp.json()["jwks_uri"]
            self.jwks_client = jwt.PyJWKClient(jwks_uri)

    async def decode_token(self, token: str):
        if self.jwks_client is None:
            await self.refresh_keys()

        logger.debug("Fetching JWT Signing Key")
        signing_key = await asyncio.to_thread(self.jwks_client.get_signing_key_from_jwt, token)

        logger.debug("Decoding and Verifying JWT")
        try:
            return await asyncio.to_thread(
                jwt.decode,
                jwt=token,
                key=signing_key.key,
                algorithms=[config.JWT_ALG],
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "require": ["sub"]
                },
            )
        except jwt.exceptions.InvalidIssuerError:
            logger.debug("Internal issuer validation failed, trying external issuer")
            return await asyncio.to_thread(
                jwt.decode,
                jwt=token,
                key=signing_key.key,
                algorithms=[config.JWT_ALG],
                issuer=self.external_issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "require": ["sub"]
                },
            )

jwt_manager = JwtManager()
