#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import datetime
import getpass
from pathlib import Path
def run_command(command, check=True):
    result = subprocess.run(command, shell=True, text=True, capture_output=True, check=check)
    return result
def get_input(prompt, default=None):
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()
def main():
    if os.geteuid() != 0:
        print("Этот скрипт должен быть запущен с правами суперпользователя (sudo)")
        sys.exit(1)
    print("=== Установка и настройка Samba ===")
    run_command("apt update")
    run_command("apt install -y samba samba-common-bin")
    smb_conf = "/etc/samba/smb.conf"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = f"{smb_conf}.backup.{timestamp}"
    if os.path.exists(smb_conf):
        shutil.copy2(smb_conf, backup_file)
    try:
        current_user = subprocess.getoutput("logname")
        if not current_user:
            current_user = getpass.getuser()
    except:
        current_user = getpass.getuser()
    share_path = get_input("Введите путь к директории общего доступа", "/srv/samba/share")
    os.makedirs(share_path, exist_ok=True)
    run_command(f"chmod 777 {share_path}")
    run_command(f"chown {current_user}:{current_user} {share_path}")
    workgroup = get_input("Введите рабочую группу", "WORKGROUP")
    server_name = get_input("Введите имя сервера", "debian-samba")
    share_name = get_input("Введите имя общего ресурса", "share")
    config = f"""[global]
   workgroup = {workgroup}
   server string = Samba Server %v
   netbios name = {server_name}
   security = user
   map to guest = bad user
   dns proxy = no
[{share_name}]
   path = {share_path}
   browsable = yes
   writable = yes
   guest ok = yes
   read only = no
   create mask = 0777
   directory mask = 0777
"""
    with open(smb_conf, 'w') as f:
        f.write(config)
    add_user = get_input("Добавить пользователя в Samba? (y/n)", "y")
    if add_user.lower() == 'y':
        smb_user = get_input("Введите имя пользователя", current_user)
        subprocess.run(f"smbpasswd -a {smb_user}", shell=True)
    if shutil.which("ufw"):
        run_command("ufw allow Samba", check=False)
    elif shutil.which("firewall-cmd"):
        run_command("firewall-cmd --permanent --add-service=samba", check=False)
        run_command("firewall-cmd --reload", check=False)
    run_command("systemctl restart smbd nmbd")
    run_command("systemctl enable smbd nmbd")
    ip_addr = subprocess.getoutput("hostname -I | awk '{print $1}'")
    print(f"Общий ресурс доступен по адресу: \\\\{ip_addr}\\{share_name}")
if __name__ == "__main__":
    main()