import os
import sys
import configparser
from dataclasses import dataclass

@dataclass
class Server:
    name: str
    ip: str
    username: str
    password: str
    os: str

@dataclass
class ServerConfig:
    servers: list[Server]

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        servers = []
        for section in cfg.sections():
            server = Server(name=section, ip=cfg.get(section, 'ip'), username=cfg.get(section, 'username'), password=cfg.get(section, 'password'), os=cfg.get(section, 'os'))
            servers.append(server)
        config = ServerConfig(servers=servers)
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config