from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FloatRange(Base):
    __tablename__ = "float_ranges"

    id = Column(Integer, primary_key=True, index=True)
    wear = Column(String)
    drop_down_index = Column(Integer)
    option_index = Column(Integer)
    button_text = Column(String)
    option_text = Column(String)
    option_value = Column(String)
    additional_options = Column(JSON)

    def __repr__(self):
        return f"<FloatRange(id={self.id}, wear={self.wear})>"
