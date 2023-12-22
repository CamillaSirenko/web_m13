from fastapi import Depends, HTTPException, status, Form, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.models import Contact
from src.database.db import get_db
from src.schemas import ContactCreateUpdate, ContactResponse, Token
from passlib.context import CryptContext
from dotenv import load_dotenv
from src.conf.config import config


load_dotenv()

SECRET_KEY = config.SECRET_KEY_JWT 
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["auth"])

# Dependency to get the current user based on the provided token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Contact).filter(Contact.email == email).first()
    if user is None:
        raise credentials_exception

    return user

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(email: str, password: str, db: Session):
    contact = db.query(Contact).filter(Contact.email == email).first()
    if contact and verify_password(password, contact.hashed_password):
        return contact
    return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route to register a new user
@router.post("/register", response_model=ContactResponse)
async def register_user(user: ContactCreateUpdate, db: Session = Depends(get_db)):
    existing_user = db.query(Contact).filter(Contact.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    hashed_password = pwd_context.hash(user.password)
    db_user = Contact(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return ContactResponse(**db_user.__dict__)

# Route to get the current user
@router.get("/users/me", response_model=ContactResponse)
async def get_current_user_route(current_user: Contact = Depends(get_current_user)):
    return ContactResponse(**current_user.__dict__)

# Route to obtain an access token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(username, password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


