from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner = Column(String(50))
    department = Column(String(50))
    progress = Column(Float, default=0.0)
    achievement_rate = Column(Float, default=0.0)
    score = Column(Float, default=0.0)
    status = Column(String(20), default="healthy")
    target_date = Column(Date, nullable=True)
    created_at = Column(Date, default=lambda: datetime.now().date())