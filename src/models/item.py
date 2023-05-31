from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    raw_name = Column(String)
    buff_id = Column(String, unique=True, index=True)
    wear = Column(String)
    is_stattrak = Column(Boolean)
    is_souvenir = Column(Boolean)
    item_type = Column(String)

    def __repr__(self):
        return f"<Item(raw_name={self.raw_name}, buff_id={self.buff_id}, wear={self.wear}, is_stattrak={self.is_stattrak}, is_souvenir={self.is_souvenir}, item_type={self.item_type})>"
