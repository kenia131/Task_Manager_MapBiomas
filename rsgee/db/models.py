from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from rsgee.db.factory import Base


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    code = Column(String)
    # year = Column(Integer)
    # region_id = Column(String)
    data = Column(String)
    output_id = Column(String)
    state = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)


class TaskLog(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    task = Column(Integer, ForeignKey('tasks.id'))
    state = Column(String)
    date = Column(DateTime)
    info = Column(String)
