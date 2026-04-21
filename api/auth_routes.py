from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from api.dependencies import get_auth_service
from auth.service import AuthError, AuthService
from domain.token import AccessTokenResult, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RefreshBody(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterBody, service: AuthService = Depends(get_auth_service)) -> dict[str, str]:
    try:
        user = await service.register(email=body.email, password=body.password)
    except AuthError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=TokenPair)
async def login(body: LoginBody, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        return await service.login(email=body.email, password=body.password)
    except AuthError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.post("/refresh", response_model=AccessTokenResult)
async def refresh(body: RefreshBody, service: AuthService = Depends(get_auth_service)) -> AccessTokenResult:
    try:
        return await service.refresh_access_token(body.refresh_token)
    except AuthError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
