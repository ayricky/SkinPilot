import argparse
import csv
import re
import sqlite3

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--sample', help='Create a sample CSV file', action='store_true')
args = parser.parse_args()

# Connect to the SQLite database (or create a new one if it doesn't exist)
conn = sqlite3.connect('data/csgo_items.db')
c = conn.cursor()

# Delete the existing items table if it exists
c.execute("DROP TABLE IF EXISTS items")

# Create the items table
c.execute('''CREATE TABLE IF NOT EXISTS items
             (id INTEGER PRIMARY KEY, buff_id INTEGER, name TEXT, raw_name TEXT, wear TEXT, is_stattrak BOOLEAN, is_souvenir BOOLEAN, item_type TEXT, major_year INTEGER, major TEXT, skin_line TEXT, weapon_type TEXT)''')

# Create the rare_paint_seeds and rare_skin_style_types tables
c.execute('''CREATE TABLE IF NOT EXISTS rare_paint_seeds
             (id INTEGER PRIMARY KEY, paint_seed INTEGER UNIQUE)''')

c.execute('''CREATE TABLE IF NOT EXISTS rare_skin_style_types
             (id INTEGER PRIMARY KEY, style_type TEXT UNIQUE)''')

# Function to determine item type
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
    elif "\u2605" in name:
        if any(x in name for x in ["Bayonet", "Karambit", "Knife", "Daggers"]):
            return "Knife"
        else:
            return "Gloves"
    else:
        return "Skin"

# Function to get sticker year and major
def get_item_year_major(item_name, item_type):
    if item_type not in ["Sticker", "Capsule"]:
        return None, None

    year_major_pattern = re.compile(r'([^|]+) (\d{4})')
    year_major_match = year_major_pattern.search(item_name)

    if year_major_match:
        major = year_major_match.group(1).strip().rsplit(' ', 1)[-1]
        return int(year_major_match.group(2)), major
    else:
        return None, None

# Function to get skin_line
def get_skin_line(name, item_type):
    if item_type not in ["Skin", "Knife", "Gloves"]:
        return None

    skin_line_pattern = re.compile(r'\| (.+?) \(')
    skin_line_match = skin_line_pattern.search(name)

    if skin_line_match:
        return skin_line_match.group(1).strip()
    else:
        return None

# Function to get weapon type
def get_weapon_type(name, item_type):
    if item_type not in ["Skin", "Knife", "Gloves"]:
        return None

    weapon_type_pattern = re.compile(r'^(.+?) \|')
    weapon_type_match = weapon_type_pattern.search(name)

    if weapon_type_match:
        return weapon_type_match.group(1).strip()
    else:
        return None

# Read the text file and insert the data into the database
with open('data/buffids.txt', 'r') as file:
    for line in file:
        buff_id, raw_name = line.strip().split(';', 1)
        buff_id = int(buff_id)

        # Check for wear, StatTrak, and Souvenir
        wear = re.search(r'\((.*?)\)', raw_name)
        wear = wear.group(1) if wear else None
        is_stattrak = 'StatTrak' in raw_name
        is_souvenir = 'Souvenir' in raw_name

        # Get item type
        item_type = get_item_type(raw_name)

        # Get sticker year and major
        major_year, major = get_item_year_major(raw_name, item_type)

        # Get skin line
        skin_line = get_skin_line(raw_name, item_type)

        # Get weapon type
        weapon_type = get_weapon_type(raw_name, item_type)

        # Clean up the name
        name = re.sub(r'\s*\((.*?)\)|StatTrak™ |Souvenir ', '', raw_name)

        # Insert the data into the items table
        c.execute("INSERT INTO items (buff_id, name, raw_name, wear, is_stattrak, is_souvenir, item_type, major_year, major, skin_line, weapon_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (buff_id, name, raw_name, wear, is_stattrak, is_souvenir, item_type, major_year, major, skin_line, weapon_type))


# Add the following code block to the end of the script
if args.sample:
    # Retrieve the first 10 rows from the items table
    c.execute('SELECT * FROM items LIMIT 10')

    # Get the column names from the cursor description
    column_names = [desc[0] for desc in c.description]

    # Create a CSV writer object and write the column names as the header row
    with open('data/sample.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)

        # Write each row of data to the CSV file
        for row in c:
            writer.writerow(row)

# Commit the changes and close the connection
conn.commit()
conn.close()