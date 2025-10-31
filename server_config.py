import os
import sys
import configparser
from dataclasses import dataclass

@dataclass
class Nauticock:
    username: str
    password: str
    ip: str
    command: str

@dataclass
class Server:
    name: str
    ip: str
    username: str
    password: str
    os: str
    extra_commands: list

@dataclass
class ServerConfig:
    nauticock: Nauticock
    servers: list

def load_config(config_path: os.PathLike):
    try:
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
    except Exception as e:
        print(f"Failed to load config file from {config_path}: {e}", file=sys.stderr)
        exit(1)
    try:
        nauticock = Nauticock(username=cfg.get("nauticock", "username"), password=cfg.get("nauticock", "password"),
                              ip=cfg.get("nauticock", "ip"), command=cfg.get("nauticock", "command"))
        servers = []
        for section in cfg.sections():
            if section == 'nauticock':
                continue
            if cfg.has_option(section, 'extra_commands'):
                extra_commands = cfg.get(section, 'extra_commands').split(',')
            else:
                extra_commands = []
            server = Server(name=section, ip=cfg.get(section, 'ip'), username=cfg.get(section, 'username'), password=cfg.get(section, 'password'), os=cfg.get(section, 'os'), extra_commands=extra_commands)
            servers.append(server)
        config = ServerConfig(nauticock=nauticock, servers=servers)
    except Exception as e:
        print(f"Error in config file {config_path}: {e}", file=sys.stderr)
        exit(1)
    return config