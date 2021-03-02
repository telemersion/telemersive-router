# Telemersive Router

Telemersive Router that contains an telemersive-broker and the telemersive-manager.

## Installation
To install the telemersive router on an instance clone the github repository into the installation directory (for example `/opt/telemersive-router`).

```
git clone https://gitlab.zhdk.ch/iaspace/05_projects/telemersive-router
```

Important for the installation is that first the broker is installed and second the manager.

### Broker

To install the mosquitto broker as a service (Debian with systemd) use the following command:

```bash
sudo ./broker-service-install.sh
```
### Manager

Installs the manager together with NPM if it is not installed already.

```bash
sudo ./manager-service-install.sh
```

## Configuration

### Change Credentials

#### Broker

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

#### Manager

```bash
cd manager
```

Copy `access.js.template` to `access.js` and adjust credentials:

```
module.exports.broker_url = 'telemersive.zhdk.ch';
module.exports.broker_port = 3883;
module.exports.switch_port = 3591;
module.exports.user = 'manager';
module.exports.pwd = 'manager';
```

## Update

To update please first stop the service to not break the running service and later start it again.

### Manager

To update to a newer version change to the manager directory and update the npm project:

```bash
git pull
cd manager
npm install
```

## Usage

### Broker

To test the mosquitto broker it is possible to run it without service installation:

```bash
./broker-run.sh
```

#### Service

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

### Manager

To run the manager without the service use the following script:

```bash
./manager-run.sh
```

#### Service

```bash
# start service
sudo systemctl start telemersive-manager.service

# stop service
sudo systemctl stop telemersive-manager.service

# restart service
sudo systemctl restart telemersive-manager.service

# enable service (auto-start on restart)
sudo systemctl enable telemersive-manager.service

# disbale service
sudo systemctl disable telemersive-manager.service

# show status
sudo systemctl status telemersive-manager.service
```

## Uninstall

### Broker

```bash
sudo ./broker-service-uninstall.sh
```

### Manager

```bash
sudo ./manager-service-uninstall.sh.sh
```

## Credits

- Florian Bruggisser
- Martin Fröhlich
