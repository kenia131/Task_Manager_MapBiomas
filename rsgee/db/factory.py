from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base()


class DatabaseManager():
    def __init__(self, settings):
        db = '{ENGINE}://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format(**settings)
        self.__engine = create_engine(db, convert_unicode=True)

    def get_session(self):
        session = scoped_session(
            sessionmaker(autocommit=False, autoflush=True, bind=self.__engine))
        return session

    def migrate(self):
        session = self.get_session()
        Base.metadata.drop_all(bind=self.__engine)
        Base.metadata.create_all(bind=self.__engine)
        session.commit()
