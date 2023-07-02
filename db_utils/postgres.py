import argparse
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, MetaData, ForeignKey, select

import pandas as pd

POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

class CSItemsDatabase:
    def __init__(self):
        self.engine = create_engine(f'postgresql://skinpilot:{POSTGRES_PASSWORD}@0.0.0.0:5432/skinpilot_db')
        self.connection = self.engine.connect()
        self.metadata = MetaData()

    def create_items_table(self):
        items = Table(
            'items',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('buff_id', Integer, unique=True),
            Column('name', String),
            Column('raw_name', String),
            Column('wear', String),
            Column('is_stattrak', Boolean),
            Column('is_souvenir', Boolean),
            Column('item_type', String),
            Column('major_year', Integer),
            Column('major', String),
            Column('skin_line', String),
            Column('weapon_type', String),
        )
        self.metadata.create_all(self.engine)

    def insert_item(self, item_data):
        items = self.metadata.tables['items']
        self.connection.execute(items.insert(), item_data)

    def get_items(self, limit=None):
        items = self.metadata.tables['items']
        query = select([items])
        if limit:
            query = query.limit(limit)
        return self.connection.execute(query).fetchall()

    def create_buff163_table(self):
        buff163 = Table(
            'buff163',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('skin_line', String),
            Column('drop_down_index', Integer),
            Column('option_index', Integer),
            Column('button_text', String),
            Column('option_text', String),
            Column('option_value', String),
            Column('additional_options', String),
        )
        self.metadata.create_all(self.engine)

    def insert_buff163_data(self, buff163_data):
        buff163 = self.metadata.tables['buff163']
        self.connection.execute(buff163.insert(), buff163_data.to_dict('records'))

    def load_buff163_data(self, csv_file):
        buff163_data = pd.read_csv(csv_file)
        buff163_data = buff163_data.drop(
            columns=["buff_id", "raw_name", "wear"]
        )  # Remove buff_id, raw_name, and wear columns
        buff163_data = buff163_data.drop_duplicates()  # Keep unique rows
        self.insert_buff163_data(buff163_data)

    def sort_buff163_by_name(self):
        buff163 = self.metadata.tables['buff163']
        query = select([buff163.c]).order_by(buff163.c.name, buff163.c.button_text, buff163.c.option_index)
        sorted_data = self.connection.execute(query).fetchall()
        self.connection.execute(buff163.delete())
        self.connection.execute(buff163.insert(), [dict(row) for row in sorted_data])

    def remove_float_range_rows(self):
        buff163 = self.metadata.tables['buff163']
        self.connection.execute(buff163.delete().where(buff163.c.button_text == 'Float Range'))

    def create_float_ranges_table(self):
        float_ranges = Table(
            'float_ranges',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('wear', String),
            Column('drop_down_index', Integer),
            Column('option_index', Integer),
            Column('button_text', String),
            Column('option_text', String),
            Column('option_value', String),
            Column('additional_options', String),
        )
        self.metadata.create_all(self.engine)


    def insert_float_ranges_data(self, float_ranges_data):
        float_ranges = self.metadata.tables['float_ranges']
        self.connection.execute(float_ranges.insert(), float_ranges_data.to_dict('records'))

    def load_float_ranges_data(self, csv_file):
        float_ranges_data = pd.read_csv(csv_file)
        float_ranges_data = float_ranges_data[float_ranges_data['button_text'] == 'Float Range']
        self.insert_float_ranges_data(float_ranges_data)
    
    def create_all(self):
        self.create_items_table()
        self.create_buff163_table()
        self.load_buff163_data("data/buff163_data.csv")
        self.sort_buff163_by_name()
        self.remove_float_range_rows()
        self.create_float_ranges_table()
        self.load_float_ranges_data("data/cs_items_float_ranges.csv")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CS Items Database')
    args = parser.parse_args()

    db = CSItemsDatabase()
    db.create_all()
    