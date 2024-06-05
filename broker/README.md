# Telemersive Broker

*broker* contains the telemersive-broker and is the third component of the *Telemersive Router*

## Installation

To install the mosquitto broker as a service (Debian with systemd) use the following commands as root:

```bash
cd /broker
./broker-service-install.sh
```

## Configuration

### Change Credentials

```bash
cd broker
```

Edit the `users.pwd`:

```
manager:password
peer:password
```

To encryp the passwords, run the following script:

```bash
./encrypt-userlist.sh
```

## Update

To update please first stop the service to not break the running service and later start it again.

To test the mosquitto broker it is possible to run it without service installation:

```bash
./broker-run.sh
```

### Service

```bash
# start service
sudo systemctl start telemersive-broker.service

# stop service
sudo systemctl stop telemersive-broker.service

# restart service
sudo systemctl restart telemersive-broker.service

# enable service (auto-start on restart)
sudo systemctl enable telemersive-broker.service

# disbale service
sudo systemctl disable telemersive-broker.service

# show status
sudo systemctl status telemersive-broker.service
```

## Uninstall


```bash
sudo ./broker/broker-service-uninstall.sh
```

## Credits

Scripts:
* Florian Bruggisser 

