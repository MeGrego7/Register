from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from Database import Base, engine
from datetime import datetime
from sqlalchemy.orm import relationship

class UserDB(Base):
    __tablename__ = "User"
    ID = Column(Integer, primary_key=True)
    Team_Name = Column(String)
    Hashed_Password = Column(String)
    Email = Column(String, unique=True)
    Created_At = Column(DateTime, default=datetime.now())

class MemberDB(Base):
    __tablename__ = "Member"
    ID = Column(Integer, primary_key=True)
    Captain_ID = Column(Integer, ForeignKey("User.ID", ondelete="CASCADE"), nullable=False)
    NISN = Column(String, unique=True)
    Full_Name = Column(String, unique=True)
    Created_At = Column(DateTime, default=datetime.now())
    Gender = Column(String)
    Birthdate = Column(DateTime)

Base.metadata.create_all(engine)