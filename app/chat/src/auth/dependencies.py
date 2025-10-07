import jwt
from fastapi import (
    status,
    HTTPException,
    Depends
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_PUB_KEY
from auth.token import decode_jwt


bearer_scheme = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependency to be used by FastAPI endpoints.

    Raises HTTPException if there's no JWT present
    in the headers or if a server error occurs.
    """
    if JWT_PUB_KEY is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing JWT key"
        )

    if credentials is None or credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = credentials.credentials
    try:
        payload = decode_jwt(token)
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
