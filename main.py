import time

import paramiko
import logging
import os
import config
import signal
import subprocess
import sys
from datetime import datetime

from config import Network

logger = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CFG_PATH = os.path.join(SCRIPT_PATH, "config.cfg")
DEFAULT_LOG_PATH = os.path.join(SCRIPT_PATH, "update.log")
config = config.load_config(DEFAULT_CFG_PATH)

TIME_LIMIT = 5 * 60

def makeLogger(logFile):
    formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    fh = logging.FileHandler(logFile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(stdout_handler)
    return logger

def update_libraries(client: paramiko.SSHClient, password):
    try:
        os = client.exec_command(". /etc/os-release && echo $NAME")[1].read().decode('utf-8').strip()
        logger.info(f"Found OS \"{os}\"")
        if os in config.os_dict:
            commands = config.os_dict[os]
            for command in commands:
                start_time = datetime.now()
                stdin, stdout, stderr = client.exec_command(f"echo \"{password}\" | {command}")
                channel = stdout.channel
                while not channel.exit_status_ready():
                    if (datetime.now() - start_time).total_seconds() >= TIME_LIMIT:
                        return "Timed out"
                err = stderr.read().decode('utf-8')
            return "Libraries updated"
        else:
            logger.warning(f"OS \"{os}\" not in config")
            return "OS not in config"
    except Exception as e:
        logger.error(e)
        return "Unable to update"

def update_network(network: Network):
    output = f"[{'.'.join([ str(n) for n in network.network])}/{network.netmask_num}]\n"
    num_servers = 1 << (32 - network.netmask_num)
    netmask = network.netmask
    for i in range(1, num_servers):
        ip = network.network
        ip = [(ip[0] & netmask[0]) + ((i >> 24) & 255), (ip[1] & netmask[1]) + ((i >> 8) & 255), (ip[2] & netmask[2]) + ((i >> 8) & 255), (ip[3] & netmask[3]) + (i & 255)]
        ip = '.'.join([str(num) for num in ip])
        if ip in config.ignore:
            continue
        logger.info(f"SSHing into {ip}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(ip, username=config.auth.username, password=config.auth.password, timeout=2)
            result = update_libraries(client, config.auth.password)
            logger.info(result)
            output += f"  {ip}: {result}\n"
        except Exception as e:
            continue
    return output

def notify_discord(output):
    subprocess.run(f"{config.nauticock.command} --text \"\" --mono \"{output}\"", shell=True)

def update_networks():
    for network in config.networks:
        output = update_network(network)
        output += "\n"
        notify_discord(output)

if __name__ == '__main__':
    logger = makeLogger(DEFAULT_LOG_PATH)
    update_networks()