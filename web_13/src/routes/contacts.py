from fastapi import Depends, HTTPException, status, Form, APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.database.models import Contact 
from src.database.db import get_db
from src.schemas import ContactCreateUpdate, ContactResponse
from typing import List
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy import extract
from src.services.auth import auth_service


router = APIRouter()

 
@router.post("/contacts/", response_model=ContactResponse)
def create_contact(
    contact: ContactCreateUpdate,
    db: Session = Depends(get_db),
    current_user: Contact = Depends(auth_service.get_current_user)
):
    db_contact = Contact(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return ContactResponse(**db_contact.__dict__)

@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
def upcoming_birthdays(db: Session = Depends(get_db)):
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    contacts = db.query(Contact).filter(
        extract('month', Contact.birthday) == today.month,
        extract('day', Contact.birthday) >= today.day,
        extract('day', Contact.birthday) <= next_week.day
    ).all()

    return [ContactResponse(**contact.__dict__) for contact in contacts]

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: Contact = Depends(auth_service.get_current_user)
):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse(**contact.__dict__)

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact: ContactCreateUpdate,
    db: Session = Depends(get_db),
    current_user: Contact = Depends(auth_service.get_current_user)
):
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return ContactResponse(**db_contact.__dict__)

@router.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: Contact = Depends(auth_service.get_current_user)
):
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return ContactResponse(**db_contact.__dict__)
