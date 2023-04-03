import argparse
import csv
import re
import sqlite3


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
        if any(x in name for x in ["Capsule", "Challengers", "Legends", "Patch Pack"]):
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
        elif "Case" in name and "Case Hardened" not in name or "Package" in name:
            return "Case"
        elif "Patch" in name:
            return "Patch"
        elif "★" in name:
            if any(x in name for x in ["Bayonet", "Karambit", "Knife", "Daggers"]):
                return "Knife"
            else:
                return "Gloves"
        else:
            return "Skin"

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

        weapon_type_pattern = re.compile(r"^(.+?) \|")
        weapon_type_match = weapon_type_pattern.search(name)

        if weapon_type_match:
            return weapon_type_match.group(1).strip()
        else:
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", help="Create a sample CSV file", action="store_true")
    args = parser.parse_args()

    # Create the CSItemsDatabase and CSItemsParser instances
    db = CSItemsDatabase("data/csgo_items.db")
    db.create_items_table()

    items = CSItemsParser.parse_txt_file("data/buffids.txt")

    # Insert the items into the database
    for item in items:
        db.insert_item(item)

    if args.sample:
        # Retrieve the first 10 rows from the items table
        sample_items = db.get_items(limit=10)

        # Get the column names from the cursor description
        column_names = [desc[0] for desc in db.c.description]

        # Create a CSV writer object and write the column names as the header row
        with open("data/sample.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(column_names)

            # Write each row of data to the CSV file
            for row in sample_items:
                writer.writerow(row)

    # Commit the changes and close the connection
    db.commit()
    db.close()


if __name__ == "__main__":
    main()