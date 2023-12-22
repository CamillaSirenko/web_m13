from libgravatar import Gravatar
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserModel
from fastapi import HTTPException, status

async def get_user_by_email(email: str, db: Session) -> User:
    """
    Get a user by email.

    :param email: The email address of the user.
    :param db: The database session.
    :return: The user object.
    """
    return db.query(User).filter(User.email == email).first()

async def create_user(body: UserModel, db: Session) -> User:
    """
    Create a new user.

    :param body: The user data to be created.
    :param db: The database session.
    :return: The newly created user object.
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(f"Failed to fetch Gravatar: {e}")

    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Update the user's token.

    :param user: The user object.
    :param token: The new token.
    :param db: The database session.
    """
    user.refresh_token = token
    db.commit()

async def update_user_avatar(user: User, avatar_url: str, db: Session) -> None:
    """
    Update the user's avatar.

    :param user: The user object.
    :param avatar_url: The new avatar URL.
    :param db: The database session.
    """
    user.avatar = avatar_url
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()