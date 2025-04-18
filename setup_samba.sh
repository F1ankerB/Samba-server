#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Запустите скрипт с правами суперпользователя (sudo)"
  exit 1
fi
apt update
apt install -y samba samba-common-bin
cp /etc/samba/smb.conf /etc/samba/smb.conf.backup.$(date +%Y%m%d%H%M%S)
CURRENT_USER=$(logname || whoami)
read -p "Введите путь к директории общего доступа [/srv/samba/share]: " SHARE_PATH
SHARE_PATH=${SHARE_PATH:-/srv/samba/share}
mkdir -p "$SHARE_PATH"
chmod 777 "$SHARE_PATH"
chown $CURRENT_USER:$CURRENT_USER "$SHARE_PATH"
read -p "Введите рабочую группу [WORKGROUP]: " WORKGROUP
WORKGROUP=${WORKGROUP:-WORKGROUP}
read -p "Введите имя сервера [debian-samba]: " SERVER_NAME
SERVER_NAME=${SERVER_NAME:-debian-samba}
read -p "Введите имя общего ресурса [share]: " SHARE_NAME
SHARE_NAME=${SHARE_NAME:-share}
cat > /etc/samba/smb.conf << EOL
[global]
   workgroup = $WORKGROUP
   server string = Samba Server %v
   netbios name = $SERVER_NAME
   security = user
   map to guest = bad user
   dns proxy = no
[$SHARE_NAME]
   path = $SHARE_PATH
   browsable = yes
   writable = yes
   guest ok = yes
   read only = no
   create mask = 0777
   directory mask = 0777
EOL
read -p "Добавить пользователя в Samba? (y/n): " ADD_USER
if [[ "$ADD_USER" =~ ^[Yy]$ ]]; then
  read -p "Введите имя пользователя [$CURRENT_USER]: " SMB_USER
  SMB_USER=${SMB_USER:-$CURRENT_USER}
  smbpasswd -a $SMB_USER
fi
if command -v ufw > /dev/null; then
  ufw allow Samba
elif command -v firewalld > /dev/null; then
  firewall-cmd --permanent --add-service=samba
  firewall-cmd --reload
fi
systemctl restart smbd nmbd
systemctl enable smbd nmbd
echo "Samba настроен и запущен!"
echo "Общий ресурс доступен по адресу: \\\\$(hostname -I | awk '{print $1}')\\$SHARE_NAME"