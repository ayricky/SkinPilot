import json
import re
from collections import OrderedDict

import yaml

yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_dict(data.items()))

def load_skin_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def process_items(items):
    result = {}
    for item in items:
        weapon_type = item['type']
        weapon_name = item['name']
        skins = item['skins']

        if weapon_type not in result:
            result[weapon_type] = {}

        result[weapon_type][weapon_name] = {
            skin['name']: {'fullName': skin['fullName']} for skin in skins
        }

    return result

def process_stickers(stickers):
    result = {'Other': {}, 'Majors': {}}
    for sticker_name, sticker_data in stickers.items():
        if '|' in sticker_name:
            group_name = sticker_name.split('|')[1].strip()
            year_match = re.search(r'\d{4}', group_name)
            if year_match:
                year = year_match.group()
                major_name = group_name.replace(year, "").strip()
                if major_name not in result['Majors']:
                    result['Majors'][major_name] = {}
                if year not in result['Majors'][major_name]:
                    result['Majors'][major_name][year] = {}
                result['Majors'][major_name][year][sticker_name] = {'fullName': sticker_data['name']}
            else:
                if group_name not in result:
                    result[group_name] = {}
                result[group_name][sticker_name] = {'fullName': sticker_data['name']}
        else:
            result['Other'][sticker_name] = {'fullName': sticker_data['name']}

    return result

def remove_items(result, items_to_remove):
    for item in items_to_remove:
        result.pop(item)

def sort_dict(d):
    return OrderedDict(sorted((k, sort_dict(v) if isinstance(v, dict) else v) for k, v in d.items()))

def save_data_to_yaml(data, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, sort_keys=False)

def main():
    skin_data = load_skin_data('data/skin_data/skin_data.json')
    
    items = skin_data['baseWeapons']
    result = process_items(items)

    remove_items(result, ['Grenade', 'Melee', 'C4', 'Equipment'])

    Knives = result.pop('Knife')
    remove_items(Knives, ['Bare Hands', 'Knife'])

    Gloves = result.pop('Gloves')
    remove_items(Gloves, ['Default CT Gloves', 'Default T Gloves'])

    Guns = result

    stickers = skin_data['stickers']
    Stickers = process_stickers(stickers)

    data = {
        "Knives": sort_dict(Knives),
        "Gloves": sort_dict(Gloves),
        "Guns": sort_dict(Guns),
        "Stickers": sort_dict(Stickers)
    }

    save_data_to_yaml(data, 'data/skin_data/filtered_skin_data.yaml')

if __name__ == "__main__":
    main()


