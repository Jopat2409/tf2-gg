from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
import os

engine = create_engine(f'sqlite:///{os.environ.get("db", "dev.db")}')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db() -> bool:
    import models
    Base.metadata.create_all(bind=engine)

def teardown_db() -> bool:
    Base.metadata.drop_all(engine)
