import json
import re
from collections import OrderedDict

import yaml

yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_dict(data.items()))

def load_skin_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def process_items(items):
    full_names = []
    for item in items:
        skins = item['skins']
        for skin in skins:
            full_names.append(skin['fullName'])

    return full_names

def process_stickers(stickers):
    full_names = []
    for sticker_name, sticker_data in stickers.items():
        full_names.append('Sticker | ' + sticker_data['name'])

    return full_names

def remove_items(items, items_to_remove):
    return [item for item in items if item not in items_to_remove]

def save_data_to_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def main():
    skin_data = load_skin_data('data/skin_data/skin_data.json')
    
    items = skin_data['baseWeapons']
    items_full_names = process_items(items)

    stickers = skin_data['stickers']
    stickers_full_names = process_stickers(stickers)

    full_names_list = items_full_names + stickers_full_names

    items_to_remove = ['Grenade', 'Melee', 'C4', 'Equipment', 'Bare Hands', 'Knife', 'Default CT Gloves', 'Default T Gloves']
    full_names_filtered = remove_items(full_names_list, items_to_remove)

    save_data_to_json(full_names_filtered, 'data/skin_data/full_names.json')

if __name__ == "__main__":
    main()
