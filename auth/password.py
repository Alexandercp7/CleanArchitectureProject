import bcrypt


def hash_password(plain: str) -> str:
    encoded_password = plain.encode("utf-8")
    hashed_password = bcrypt.hashpw(encoded_password, bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    encoded_password = plain.encode("utf-8")
    encoded_hash = hashed.encode("utf-8")
    return bcrypt.checkpw(encoded_password, encoded_hash)