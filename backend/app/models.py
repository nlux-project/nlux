from sqlalchemy import Column, Text, Index
from .database import Base


class Record(Base):
    __tablename__ = "records"

    uri = Column(Text, primary_key=True, index=True)
    type = Column(Text, nullable=False, index=True)
    label = Column(Text, nullable=True)
    search_text = Column(Text, nullable=True)  # label + descriptions concatenated for FTS
    data = Column(Text, nullable=False)  # full JSON-LD stored as string
