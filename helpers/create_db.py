import argparse
import csv
import re
import sqlite3

import pandas as pd


class CSItemsDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()

    def create_items_table(self):
        self.c.execute("DROP TABLE IF EXISTS items")
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY, buff_id INTEGER, name TEXT, raw_name TEXT, wear TEXT, is_stattrak BOOLEAN, is_souvenir BOOLEAN, item_type TEXT, major_year INTEGER, major TEXT, skin_line TEXT, weapon_type TEXT)"""
        )

    def insert_item(self, item_data):
        self.c.execute(
            "INSERT INTO items (buff_id, name, raw_name, wear, is_stattrak, is_souvenir, item_type, major_year, major, skin_line, weapon_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            item_data,
        )

    def get_items(self, limit=None):
        query = "SELECT * FROM items"
        if limit:
            query += f" LIMIT {limit}"
        self.c.execute(query)
        return self.c.fetchall()

    def create_buff163_table(self):
        self.c.execute("DROP TABLE IF EXISTS buff163")
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS buff163
                 (id INTEGER PRIMARY KEY, name TEXT, skin_line TEXT, drop_down_index INTEGER, option_index INTEGER, button_text TEXT, option_text TEXT, option_value TEXT, additional_options TEXT, FOREIGN KEY (name) REFERENCES items (name))"""
        )

    def insert_buff163_data(self, buff163_data):
        buff163_data = buff163_data.drop(
            columns=["buff_id", "raw_name", "wear"]
        )  # Remove buff_id, raw_name, and wear columns
        buff163_data = buff163_data.drop_duplicates()  # Keep unique rows
        for row in buff163_data.itertuples(index=False):
            self.c.execute(
                "INSERT INTO buff163 (name, skin_line, drop_down_index, option_index, button_text, option_text, option_value, additional_options) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )

    def load_buff163_data(self, csv_file):
        buff163_data = pd.read_csv(csv_file)
        self.insert_buff163_data(buff163_data)

    # def remove_all_option_rows(self):
    #     self.c.execute("DELETE FROM buff163 WHERE option_text = 'All'")

    def sort_buff163_by_name(self):
        self.c.execute(
            "CREATE TEMPORARY TABLE buff163_sorted AS SELECT * FROM buff163 ORDER BY name, button_text, option_index"
        )
        self.c.execute("DROP TABLE buff163")
        self.c.execute(
            "CREATE TABLE buff163 (id INTEGER PRIMARY KEY, name TEXT, skin_line TEXT, drop_down_index INTEGER, option_index INTEGER, button_text TEXT, option_text TEXT, option_value TEXT, additional_options TEXT, FOREIGN KEY (name) REFERENCES items (name))"
        )
        self.c.execute(
            "INSERT INTO buff163 (name, skin_line, drop_down_index, option_index, button_text, option_text, option_value, additional_options) SELECT name, skin_line, drop_down_index, option_index, button_text, option_text, option_value, additional_options FROM buff163_sorted"
        )
        self.c.execute("DROP TABLE buff163_sorted")

    def remove_float_range_rows(self):
        self.c.execute("DELETE FROM buff163 WHERE button_text = 'Float Range'")

    def create_float_ranges_table(self):
        self.c.execute("DROP TABLE IF EXISTS float_ranges")
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS float_ranges
                 (id INTEGER PRIMARY KEY, wear TEXT, drop_down_index INTEGER, option_index INTEGER, button_text TEXT, option_text TEXT, option_value TEXT, additional_options TEXT, FOREIGN KEY (wear) REFERENCES items (wear))"""
        )

    def load_float_ranges_data(self, csv_file):
        float_ranges_data = pd.read_csv(csv_file)
        self.insert_float_ranges_data(float_ranges_data)

    def insert_float_ranges_data(self, float_ranges_data):
        for row in float_ranges_data.itertuples(index=False):
            self.c.execute(
                "INSERT INTO float_ranges (wear, drop_down_index, option_index, button_text, option_text, option_value, additional_options) VALUES (?, ?, ?, ?, ?, ?, ?)",
                row,
            )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class CSItemsParser:
    @staticmethod
    def parse_txt_file(txt_file):
        items = []
        with open(txt_file, "r") as file:
            for line in file:
                buff_id, raw_name = line.strip().split(";", 1)
                buff_id = int(buff_id)

                # Parse item details
                item_data = CSItemsParser.parse_item_details(raw_name)
                item_data = (buff_id, *item_data)

                items.append(item_data)

        return items

    @staticmethod
    def parse_item_details(raw_name):
        # Check for wear, StatTrak, and Souvenir
        wear = re.search(r"\((.*?)\)", raw_name)
        wear = wear.group(1) if wear else None
        is_stattrak = "StatTrak" in raw_name
        is_souvenir = "Souvenir" in raw_name

        # Get item type
        item_type = CSItemsParser.get_item_type(raw_name)

        # Get sticker year and major
        major_year, major = CSItemsParser.get_item_year_major(raw_name, item_type)

        # Get skin line
        skin_line = CSItemsParser.get_skin_line(raw_name, item_type)

        # Get weapon type
        weapon_type = CSItemsParser.get_weapon_type(raw_name, item_type)

        # Clean up the name
        name = re.sub(r"\s*\((.*?)\)|StatTrak™ |Souvenir ", "", raw_name)

        return name, raw_name, wear, is_stattrak, is_souvenir, item_type, major_year, major, skin_line, weapon_type

    @staticmethod
    def get_item_type(name):
        wear = re.search(r"\((.*?)\)", name)
        wear = wear.group(1) if wear else None

        skin_weapons = [
            "Nova",
            "M4A4",
            "P250",
            "Tec-9",
            "MAC-10",
            "AUG",
            "CZ75-Auto",
            "MP9",
            "Dual Berettas",
            "Five-SeveN",
            "Desert Eagle",
            "Glock-18",
            "USP-S",
            "P2000",
            "MP7",
            "M249",
            "AK-47",
            "AWP",
            "FAMAS",
            "G3SG1",
            "Galil AR",
            "M4A1-S",
            "MAG-7",
            "Negev",
            "P90",
            "PP-Bizon",
            "R8 Revolver",
            "SCAR-20",
            "SG 553",
            "SSG 08",
            "Sawed-Off",
            "UMP-45",
            "XM1014",
            "MP5-SD",
        ]

        if any(x in name for x in ["Capsule", "Challengers", "Legends", "Patch Pack", "2020 RMR Contenders"]):
            return "Capsule"
        elif "Sticker" in name:
            return "Sticker"
        elif "Pin" in name:
            return "Pin"
        elif "Music Kit" in name:
            return "Music Kit"
        elif "Pass" in name and "Overpass" not in name:
            return "Pass"
        elif "Graffiti" in name:
            return "Graffiti"
        elif (
            any(x in name for x in ["Case", "Package", "Parcel", "Pallet of Presents", "Radicals Box"])
            and "Case Hardened" not in name
        ):
            return "Case"
        elif "Patch" in name:
            return "Patch"
        elif "★" in name:
            if any(x in name for x in ["Bayonet", "Karambit", "Knife", "Daggers"]):
                return "Knife"
            else:
                return "Gloves"
        elif any(x in name for x in skin_weapons):
            return "Skin"
        else:
            return "Other"

    @staticmethod
    def get_item_year_major(item_name, item_type):
        if item_type not in ["Sticker", "Capsule"]:
            return None, None

        year_major_pattern = re.compile(r"([^|]+) (\d{4})")
        year_major_match = year_major_pattern.search(item_name)

        if year_major_match:
            major = year_major_match.group(1).strip().rsplit(" ", 1)[-1]
            return int(year_major_match.group(2)), major
        else:
            return None, None

    @staticmethod
    def get_skin_line(name, item_type):
        if item_type not in ["Skin", "Knife", "Gloves"]:
            return None

        skin_line_pattern = re.compile(r"\| (.+?) \(")
        skin_line_match = skin_line_pattern.search(name)

        if skin_line_match:
            return skin_line_match.group(1).strip()
        else:
            return None

    @staticmethod
    def get_weapon_type(name, item_type):
        if item_type not in ["Skin", "Knife", "Gloves"]:
            return None

        cleaned_name = name.replace("Souvenir ", "").replace("StatTrak™ ", "")
        weapon_type_pattern = re.compile(r"^(.+?) \|")
        weapon_type_match = weapon_type_pattern.search(cleaned_name)

        if weapon_type_match:
            return weapon_type_match.group(1).strip()
        else:
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", help="Create a sample CSV file", action="store_true")
    args = parser.parse_args()

    # Create the CSItemsDatabase and CSItemsParser instances
    db = CSItemsDatabase("data/cs_items.db")
    db.create_items_table()

    items = CSItemsParser.parse_txt_file("data/buffids.txt")

    # Insert the items into the database
    for item in items:
        db.insert_item(item)

    # Create the buff163 table and load data from the CSV file
    db.create_buff163_table()
    db.load_buff163_data("data/buff163_data.csv")

    # Load the rare_patterns data from the CSV file and insert it into the buff163 table
    db.load_buff163_data("data/rare_patterns.csv")

    # Create the float_ranges table and load data from the CSV file
    db.create_float_ranges_table()
    db.load_float_ranges_data("data/wears.csv")

    # Remove rows with 'Float Range' button_text from the buff163 table
    db.remove_float_range_rows()

    # Sort the buff163 table by name
    db.sort_buff163_by_name()

    # # Remove rows with 'All' option_text from the buff163 table
    # db.remove_all_option_rows()

    if args.sample:
        # Get the table names dynamically from the database
        db.c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in db.c.fetchall()]

        for table_name in table_names:
            sample_data = db.c.execute(f"SELECT * FROM {table_name} LIMIT 10").fetchall()
            column_names = [desc[0] for desc in db.c.description]

            with open(f"data/cs_items_{table_name}.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)

                for row in sample_data:
                    writer.writerow(row)

    # Commit the changes and close the connection
    db.commit()
    db.close()


if __name__ == "__main__":
    main()
