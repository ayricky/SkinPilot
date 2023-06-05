from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Buff163(Base):
    __tablename__ = "buff163"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    skin_line = Column(String)
    drop_down_index = Column(Integer)
    option_index = Column(Integer)
    button_text = Column(String)
    option_text = Column(String)
    option_value = Column(String)
    additional_options = Column(JSON)

    def __repr__(self):
        return f"<Buff163(id={self.id}, name={self.name})>"
