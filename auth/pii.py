from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class EmailLogContext:
    domain: str
    short_hash: str


def obscure_email(email: str) -> EmailLogContext:
    normalized_email = email.strip().lower()
    email_domain = normalized_email.split("@")[-1] if "@" in normalized_email else "invalid"
    short_hash = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()[:10]
    return EmailLogContext(domain=email_domain, short_hash=short_hash)
