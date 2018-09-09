import yaml
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


def absolute_path_from_project_root(rel_path_from_project_root):
    """Return the absolute path of an item with a relative path from the project root"""
    return os.path.join(PROJECT_ROOT, rel_path_from_project_root)


def load_yaml_config(filename):
    with open(filename, 'r') as f:
        return yaml.load(f)


def override_config_from_environment(config_dict):
    """Helper function to override config with environment variables of the same name"""

    for key in config_dict.iterkeys():
        if key in os.environ:
            env_var = os.environ[key]
            config_dict[key] = parse_numeric_env_vars(env_var)


def parse_numeric_env_vars(input_val):
    """Returns corresponding numerics based on contents of string variables"""
    if type(input_val) == str:
        if input_val in ['true', 'True']:
            return True
        elif input_val in ['false', 'False']:
            return False
        elif input_val.isdigit():
            return int(input_val)
        else:
            return input_val
    else:
        return input_val


def most_common(lst):
    return max(set(lst), key=lst.count)