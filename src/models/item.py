from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    buff_id = Column(Integer)
    name = Column(String)
    raw_name = Column(String)
    wear = Column(String)
    is_stattrak = Column(Boolean)
    is_souvenir = Column(Boolean)
    item_type = Column(String)
    major_year = Column(String)
    major = Column(String)
    skin_line = Column(String)
    weapon_type = Column(String)

    def __repr__(self):
        return f"<Item(name={self.name}, buff_id={self.buff_id}, wear={self.wear}, is_stattrak={self.is_stattrak}, is_souvenir={self.is_souvenir})>"
