import jwt
from fastapi import (
    status,
    HTTPException,
    Depends
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_manager import jwt_manager


bearer_scheme = HTTPBearer(auto_error=False)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependency to be used by FastAPI endpoints.

    Raises HTTPException if there's no valid JWT present in the headers.
    """
    if credentials is None or credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = credentials.credentials
    try:
        payload = await jwt_manager.decode_token(token)
        # return all of the claims in case I want to use later
        return payload
    except jwt.exceptions.MissingRequiredClaimError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token doesn't contain a valid subject field"
        )
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
