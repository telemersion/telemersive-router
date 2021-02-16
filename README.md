# Telemersion Server

Telemersion Server that contains an MQTT broker and the telemersion-manager.

## Installation
To install the telemersion server on an instance clone the github repository into the installation directory (for example `/opt/telemersion-server`).

```
git clone https://gitlab.zhdk.ch/iaspace/05_projects/telemersion-server
```

### Mosquitto Broker Service

To install the mosquitto broker as a service (Debian with systemd) use the following command:

```bash
sudo ./broker-service-install.sh
```
### Manager Service
tdb

## Usage

### Mosquitto Broker

To test the mosquitto broker it is possible to run it without service installation:

```bash
./broker-run.sh
```

#### Service

```bash
# start service
sudo systemctl start telemersion-broker.service

# stop service 
sudo systemctl start telemersion-broker.service

# restart service
sudo systemctl restart telemersion-broker.service

# enable service (auto-start on restart)
sudo systemctl enable telemersion-broker.service

# disbale service
sudo systemctl disable telemersion-broker.service

# show status
sudo systemctl status telemersion-broker.service
```

### Manager
tbd