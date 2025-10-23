import os
import sys
import configparser
from dataclasses import dataclass

@dataclass
class OS:
    name: str
    lib_update: list[str]
    distro_check: str
    distro_check_neg: str
    distro_check_pos: str

@dataclass
class OSConfig:
    os_dict: dict

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        os_dict = {}
        for section in cfg.sections():
            os_dict[section] = OS(name=section, lib_update=cfg.get(section, 'lib_update').split(','), distro_check=cfg.get(section, 'distro_check'), distro_check_neg=cfg.get(section, 'distro_check_neg'), distro_check_pos=cfg.get(section, 'distro_check_pos'))
        config = OSConfig(os_dict=os_dict)
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config