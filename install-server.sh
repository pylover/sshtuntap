#! /usr/bin/env bash


INSTANCE="sshtuntap"
USERNAME="root"
CONFIGFILE="/etc/${INSTANCE}.yml"
PYTHON=$(which python3.6)
PIP=$(which pip3.6)

if [ -z $PIP ]; then
	curl https://bootstrap.pypa.io/get-pip.py | sudo -H $PYTHON
	PIP=$(which pip3.6)
fi

sudo -H $PIP install .
sudo -H ssh-tuntap-server setup

echo "
[Unit]
Description=sshtuntap initializer
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/ssh-tuntap-server -c ${CONFIGPATH} initialize
RemainAfterExit=true
ExecStop=/usr/local/bin/ssh-tuntap-server -c ${CONFIGPATH} dispose
StandardOutput=journal

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/${INSTANCE}.service >> /dev/null

sudo systemctl daemon-reload
sudo systemctl enable ${INSTANCE}.service
sudo service ${INSTANCE} start

