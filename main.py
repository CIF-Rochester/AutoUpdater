import time

import paramiko
import logging
import os

import select

import os_config
import server_config

logger = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SERVER_CFG_PATH = os.path.join(SCRIPT_PATH, "server_config.cfg")
DEFAULT_OS_CFG_PATH = os.path.join(SCRIPT_PATH, "os_config.cfg")
server_cfg = server_config.load_config(DEFAULT_SERVER_CFG_PATH)
os_cfg = os_config.load_config(DEFAULT_OS_CFG_PATH)

def update_libraries(client: paramiko.SSHClient, password, command: str):
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        stdin.write(f'{password}\n')
        channel = stdout.channel
        while not channel.exit_status_ready():
            pass
        if stderr.read():
            return "Error running library update command"
        return "Libraries updated"
    except Exception as e:
        return "Unable to run library update command"

def check_distro(client: paramiko.SSHClient, password: str, command: str, pos: str, neg: str):
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        stdin.write(password + '\n')
        if stderr.read():
            return "Error running distro check command"
        output = stdout.read().decode("utf-8")
        if pos in output:
            lines = output.split('\n')
            for line in lines:
                if pos in line:
                    return line
            return "Unable to determine if new distro is available"
        elif neg in output:
            return "Distro is up-to-date"
        else:
            "Unable to determine if new distro is available"
    except Exception as e:
        return "Unable to run distro check command"

def update_server(server: server_config.Server, os: os_config.OS):
    ip = server.ip
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        logger.info(f"Attempting SSH connection to {ip}")
        client.connect(ip, username=server.username,password=server.password)
    except Exception as e:
        return f'Unable to SSH into {ip}'
    update_output = f'{server.name}\n'
    update_output += f'    {update_libraries(client, server.password, os.lib_update)}\n'
    update_output += f'    {check_distro(client, server.password, os.distro_check, os.distro_check_pos, os.distro_check_neg)}\n'
    return update_output


if __name__ == '__main__':
    for server in server_cfg.servers:
        print(update_server(server, os_cfg.os_dict[server.os]))