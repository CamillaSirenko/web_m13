from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType, EmailSchema
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from src.services.auth import Auth, get_email_from_token   
from fastapi_mail import EmailSchema
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv
from src.conf.config import config
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi.routing import Request
import os
import uvicorn
import cloudinary


load_dotenv()

app = FastAPI()
auth_service = Auth()


cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_USERNAME,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="TODO Systems",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


 
# Налаштування обмежень
limiter = FastAPILimiter(
    key_func=lambda _: "global",  # Ідентифікатор для глобального обмеження
    redis_url="redis://localhost:6379/0",   
)
 
@app.get("/contacts/", dependencies=[Depends(RateLimiter(times=5, minutes=1))])
async def read_contacts():
    return {"message": "Read contacts"}

 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/user/contacts/", dependencies=[Depends(RateLimiter(times=5, minutes=1))])
async def read_user_contacts(token: str = Depends(oauth2_scheme)):
    return {"message": "Read user contacts"}

# Застосування глобального обмеження на швидкість для всіх маршрутів
@app.middleware("http")
async def limiter_middleware(request: Request, call_next):
    await limiter.init()
    response = await call_next(request)
    await limiter.close()
    return response

# Додавання обробника помилок для обробки випадку перевищення обмежень
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail}

async def get_current_email(token: str = Depends(auth_service.oauth2_scheme)):
    return await get_email_from_token(token)

@app.post("/send-email")
async def send_in_background(
    background_tasks: BackgroundTasks,
    body: EmailSchema,
    current_email: str = Depends(get_current_email),   
):
    message = MessageSchema(
        subject="Fastapi mail module",
        recipients=[body.email],
        template_body={"fullname": "Billy Jones"},
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message, template_name="example_email.html")

    return {"message": "email has been sent"}


@app.post("/upload-avatar/")
async def upload_avatar(file: UploadFile):
    # Отримати завантажене зображення
    contents = await file.read()

    # Завантажити зображення на Cloudinary
    response = upload(contents, folder="avatars")

    if response.get("public_id"):
         
        url, options = cloudinary_url(response["public_id"], format="png")
        return {"avatar_url": url}
    else:
        raise HTTPException(
            status_code=500, detail="Failed to upload avatar to Cloudinary"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
