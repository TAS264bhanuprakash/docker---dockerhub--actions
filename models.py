from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    reset_token = Column(String, nullable=True)  # Optional field for password reset

    # One-to-one relationship with UserMetrics
    metrics = relationship("UserMetrics", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserMetrics(Base):
    __tablename__ = "user_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    logins = Column(Integer, default=0)
    password_changes = Column(Integer, default=0)

    # Back reference to the User table
    user = relationship("User", back_populates="metrics")
