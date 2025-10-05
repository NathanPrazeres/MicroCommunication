import config
import jwt


def decode_jwt(token: str | bytes) -> dict:
    """
    Decode JWT.
    List of errors found here:
        - https://pyjwt.readthedocs.io/en/stable/api.html#exceptions
    """
    return jwt.decode(
        jwt=token,
        key=config.JWT_PUB_KEY,
        algorithms=[config.JWT_ALG],
        options={"verify_signature": True, "require": ["sub"]}, # require the subject claim to be present
    )
