import math
import os
import sys
import configparser
from dataclasses import dataclass

@dataclass
class Nauticock:
    command: str

@dataclass
class Auth:
    username: str
    password: str

@dataclass
class Network:
    network: list
    netmask: list
    netmask_num: int

@dataclass
class Config:
    nauticock: Nauticock
    auth: Auth
    networks: list
    os_dict: dict
    ignore: list

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        nauticock = Nauticock(command=cfg.get("nauticock", "command"))
        auth = Auth(username=cfg.get("auth", "username"), password=cfg.get("auth", "password"))
        networks = []
        raw_networks = cfg.get("networks", "networks").split(' ')
        for raw_net in raw_networks:
            if raw_net:
                network, netmask_num = raw_net.split('/')
                network = [int(n) for n in network.split('.')]
                netmask_num = int(netmask_num)
                netmask = ((1 << netmask_num) - 1) << (32 - netmask_num);
                netmask = [(netmask >> 24) & 255, (netmask >> 16) & 255, (netmask >> 8) & 255, netmask & 255]
                networks.append(Network(network, netmask, netmask_num))
        os_dict = {}
        for section in cfg.sections():
            if section == 'nauticock' or section == 'networks' or section == 'auth':
                continue
            os_dict[section] = cfg.get(section, 'lib_update').split(',')
        config = Config(nauticock=nauticock, networks=networks, auth=auth, os_dict=os_dict, ignore=cfg.get("networks", "ignore").split(' '))
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config