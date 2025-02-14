from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str) -> str:
    return pwd_context.hash(password)


# created here to avoid importing pwd_content everywhere but upto discretion
def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
