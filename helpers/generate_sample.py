from collections import OrderedDict

import yaml


def load_yaml_data(file_path):
    with open(file_path, 'r') as file:
        return yaml.load(file, Loader=yaml.Loader)

def create_sample(data):
    sample_data = {}
    for category, groups in data.items():
        sample_data[category] = {}
        for group, instances in groups.items():
            if isinstance(instances, dict):
                if instances:
                    first_instance_key = list(instances.keys())[0]
                    sample_data[category][group] = {first_instance_key: instances[first_instance_key]}
            else:
                sample_data[category][group] = instances[:1]

    return sample_data

def save_data_to_yaml(data, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, sort_keys=False)

def main():
    data = load_yaml_data('data/skin_data/filtered_skin_data.yaml')
    sample_data = create_sample(data)
    save_data_to_yaml(sample_data, 'data/skin_data/sample.yaml')

if __name__ == "__main__":
    main()
