from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    ID: int
    Team_Name: str
    Hashed_Password: str
    Email: str
    Created_At: datetime = datetime.now()

class Member(BaseModel):
    ID: int
    Captain_ID: int
    NISN: str
    Full_Name: str
    Created_At: datetime = datetime.now()
    Gender: str
    Birthdate: datetime

class CreateMember(BaseModel):
    Captain_ID: int
    NISN: str
    Full_Name: str
    Gender: str
    Birthdate: datetime

class CreateUser(BaseModel):
    Team_Name: str
    Hashed_Password: str
    Email: str

class LoginUser(BaseModel):
    Hashed_Password: str
    Email: str
