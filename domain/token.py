from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class AccessTokenResult:
    access_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class TokenPayload:
    subject: str
    token_type: str
    jti: str
    issued_at: datetime
    expires_at: datetime
