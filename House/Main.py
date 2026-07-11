from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from Database import get_db
from Models import UserDB, MemberDB
from Schemas import User, Member, CreateMember, CreateUser, LoginUser
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from Auth import get_password_hash, verify_password, create_access_token, get_current_user
import os
 
Application = FastAPI()

@Application.post("/api/auth/signup")
def Signup(user:CreateUser, db:Session=Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.Email==user.Email).first()
    if db_user: raise HTTPException(status_code=400, detail="Email Already Exists")
    Hash_Password = get_password_hash(User.Hashed_Password)
    New_User = UserDB(
        Team_Name = user.Team_Name,
        Hashed_Password = Hash_Password,
        Email = user.Email,
    )
    db.add(New_User)
    db.commit()
    db.refresh(New_User)
    return New_User

@Application.post("/api/auth/login")
def Login(user:LoginUser, db:Session=Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.Email==user.Email).first()
    Token = create_access_token(data={"sub":user.Email})
    return {"access_token": Token, "token_type": "bearer"}

@Application.get("/api/members")
def GetMembers(db:Session=Depends(get_db)):
    query = select(UserDB)
    result = db.execute(query).scalars().all()
    return result

@Application.post("/api/members")
def AddMembers(member:CreateMember, db:Session=Depends(get_db)):
    New_Member = UserDB(
        Captain_ID = member.Captain_ID,
        NISN = member.NISN,
        Full_Name = member.Full_Name,
        Birthdate = member.Birthdate,
        Gender = member.Gender,
    )
    db.add(New_Member)
    db.commit()
    db.refresh(New_Member)
    return New_Member

@Application.get("/api/members/{id}")
def GetID(ID:int, db:Session=Depends(get_db)):
    member=db.query(MemberDB).filter(MemberDB.ID==ID).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member Not Found")
    return member

@Application.put("/api/members/{id}")
def PutID(ID:int, memberIN:CreateMember, db:Session=Depends(get_db)):
    member=db.query(MemberDB).filter(MemberDB.ID==ID).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member Not Found")
    member.Captain_ID = memberIN.Captain_ID
    member.NISN = memberIN.NISN
    member.Full_Name = memberIN.Full_Name
    member.Birthdate = memberIN.Birthdate
    member.Gender = memberIN.Gender
    db.commit()
    db.refresh(member)
    return member

@Application.delete("/api/members/{id}")
def DeleteID(ID:int, db:Session=Depends(get_db)):
    member=db.query(MemberDB).filter(MemberDB.ID==ID).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member Not Found")
    db.delete(member)
    db.commit()
    return
