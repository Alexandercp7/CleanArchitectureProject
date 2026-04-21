from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from auth.service import AuthError, AuthService
from auth.tokens import TokenError, decode_access_token
from domain.user import User


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.deps.auth_service


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    raw_token = authorization.split(" ", maxsplit=1)[1]
    try:
        payload = decode_access_token(raw_token)
    except TokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from error

    auth_service = get_auth_service(request)
    try:
        return await auth_service.get_active_user(payload.subject)
    except AuthError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized") from error


CurrentUser = Annotated[User, Depends(get_current_user)]
