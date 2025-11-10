import config
import httpx
import jwt
import asyncio
import logging
import ssl
import urllib.request

logger = logging.getLogger(__name__)


class JwtManager():
    def __init__(self):
        self.jwks_client = None
        self.issuer = None

    async def refresh_keys(self):
        logger.info("Refreshing Keycloak JWKs")
        url = f"http://{config.AUTH_SERVICE}/realms/{config.AUTH_REALM}/.well-known/openid-configuration"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()

            self.issuer = resp.json()["issuer"]
            jwks_uri = resp.json()["jwks_uri"]

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            logger.info("JWK URI:", jwks_uri)
            self.jwks_client = jwt.PyJWKClient(jwks_uri, ssl_context=ssl_context)

    async def decode_token(self, token: str):
        if self.jwks_client is None:
            await self.refresh_keys()

        logger.info("Fetching JWT Signing Key")
        signing_key = await asyncio.to_thread(self.jwks_client.get_signing_key_from_jwt, token)

        logger.info("Decoding and Verifying JWT")
        try:
            return await asyncio.to_thread(
                jwt.decode,
                jwt=token,
                key=signing_key.key,
                algorithms=[config.JWT_ALG],
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_iss": False,
                    "require": ["sub"]
                },
            )
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise


jwt_manager = JwtManager()
