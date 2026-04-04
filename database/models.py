from sqlalchemy import Column, Integer, BigInteger, DateTime, String, Float, Boolean, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    balance = Column(Integer, default=0)  # количество доступных генераций (в рублях/50)
    created_at = Column(DateTime, server_default=func.now())

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # id из таблицы users
    prompt_text = Column(String, nullable=False)
    style = Column(String)
    vocal_type = Column(String)
    audio_url1 = Column(String)
    audio_url2 = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)  # сумма в рублях
    generations_added = Column(Integer, nullable=False)
    yookassa_payment_id = Column(String, unique=True)
    status = Column(String, default="pending")  # pending, succeeded, failed
    created_at = Column(DateTime, server_default=func.now())

class GlobalCounter(Base):
    __tablename__ = "global_counter"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    count = Column(Integer, default=0)
    updated_at = Column(DateTime, onupdate=func.now())