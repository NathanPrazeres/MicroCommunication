import jwt
from fastapi import (
    status,
    HTTPException,
    Depends
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_manager import jwt_manager
import logging

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependency to be used by FastAPI endpoints.

    Raises HTTPException if there's no valid JWT present in the headers.
    """
    if credentials is None or credentials.scheme != "Bearer":
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = credentials.credentials
    try:
        payload = await jwt_manager.decode_token(token)
        logger.debug("Token verified for user: %s", payload.get("sub"))
        # return all of the claims in case I want to use later
        return payload
    except jwt.exceptions.MissingRequiredClaimError:
        logger.warning("Token missing required 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token doesn't contain a valid subject field"
        )
    except jwt.exceptions.PyJWTError as e:
        logger.warning("JWT validation failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
