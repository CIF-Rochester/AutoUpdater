import time

import paramiko
import logging
import os

import select

import os_config
import server_config
import schedule
import time
import datetime

logger = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SERVER_CFG_PATH = os.path.join(SCRIPT_PATH, "server_config.cfg")
DEFAULT_OS_CFG_PATH = os.path.join(SCRIPT_PATH, "os_config.cfg")
DEFAULT_LOG_PATH = os.path.join(SCRIPT_PATH, "update.log")
server_cfg = server_config.load_config(DEFAULT_SERVER_CFG_PATH)
os_cfg = os_config.load_config(DEFAULT_OS_CFG_PATH)

def makeLogger(logFile):
    formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

def update_libraries(client: paramiko.SSHClient, password, commands: list[str]):
    try:
        output = ''
        for command in commands:
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            stdin.write(f'{password}\n')
            channel = stdout.channel
            while not channel.exit_status_ready():
                pass
            if stderr.read():
                output = "Error running library update command"
        if len(output) == 0:
            return "Libraries updated"
        return output
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
        client.connect(ip, username=server.username,password=server.password)
    except Exception as e:
        return f'Unable to SSH into {ip}'
    update_output = f'{server.name}\n'
    update_output += f'  - {update_libraries(client, server.password, os.lib_update)}\n'
    update_output += f'  - {check_distro(client, server.password, os.distro_check, os.distro_check_pos, os.distro_check_neg)}\n'
    try:
        client.close()
    except Exception as e:
        pass
    logger.info(f"{ip} updated")
    return update_output

def notify_discord(update_info):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server_cfg.nauticock.ip, username=server_cfg.nauticock.username, password=server_cfg.nauticock.password, timeout=30)
        client.exec_command(server_cfg.nauticock.command + f" --text \"AutoUpdater updated the following servers:\" --mono \"{update_info}\"")
        client.close()
        logger.info("Report to sent to Discord")
    except Exception as e:
        logger.error("Unable to connect to notify NauticockBot")

def update_all_servers():
    logger.info(f"Server updates started at {datetime.datetime.now()}")
    update_info = ''
    for server in server_cfg.servers:
        update_info += update_server(server, os_cfg.os_dict[server.os])
    notify_discord(update_info)
    logger.info(f"Server updates finished at {datetime.datetime.now()}")

if __name__ == '__main__':
    logger = makeLogger(DEFAULT_LOG_PATH)
    # update_all_servers()
    try:
        schedule.every().friday.at("03:00").do(update_all_servers)
        while True:
            schedule.run_pending()
            time.sleep(60)
    except Exception as e:
        logger.error("A fatal error has occurred")