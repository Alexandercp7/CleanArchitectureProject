from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class User:
    id: str
    email: str
    hashed_password: str
    role: str #admin, user.