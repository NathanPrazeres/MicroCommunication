import jwt
from fastapi import (
    Response,
    status,
    Request,
)
from config import JWT_PUB_KEY
from auth.token import decode_jwt
from uuid import UUID


async def verify_token(req: Request, call_next):
    if JWT_PUB_KEY is None:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content="Missing JWT key"
        )

    auth = req.headers.get("Authorization")
    token = None
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()

    if not token:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Missing or invalid Authorization header"
        )

    try:
        payload = decode_jwt(token=token)

        # Setting the user_id in the state to be used later
        # when looking up info from the database (if needed)
        req.state.user_id = payload.get("sub")
        if req.state.user_id is None:
            raise jwt.exceptions.MissingRequiredClaimError()
    except jwt.exceptions.MissingRequiredClaimError:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Token doesn't contain a valid subject field"
        )
    except jwt.exceptions.PyJWTError:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid or expired token"
        )

    return await call_next(req)
