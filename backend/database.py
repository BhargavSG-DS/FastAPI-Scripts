from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

credentials = dotenv_values(".env")

SQLALCHEMY_DATABASE_URL = "sqlite:///./CSNB.db" # for sqlite (recommended to only use during developement)
# SQLALCHEMY_DATABASE_URL = f'mssql://LAPTOP-T4E6IV9G/CSNB?trusted_connection=yes&driver=SQL Server Native Client 11.0' # for mssql (recommended to only use for deployment)


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
# connect_args={"check_same_thread": False}
# ...is needed only for SQLite. It's not needed for other databases

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
