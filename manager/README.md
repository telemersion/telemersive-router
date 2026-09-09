# Telemersive Manager

*manager* contains the telemersive-manager


## Installation

Important for the installation is that first the broker is installed and second the manager.

Installs the manager together with NPM if it is not installed already.

```bash
cd manager
./manager-service-install.sh
```

## Configuration

### Change Credentials

```bash
cd manager
```

Copy `access.js.template` to `access.js` and fill in the broker's address and the
credentials of the account the manager connects with — the same user that
`broker/acl.conf` grants access to:

```js
module.exports.broker_url = '<broker url>';
module.exports.broker_port = 3883;
module.exports.switch_port = 3591;
module.exports.user = '<broker user>';
module.exports.pwd = '<broker password>';
```

`access.js` is gitignored, so the real values stay out of the repository.

## Update

To update please first stop the service to not break the running service and later start it again.

To update to a newer version change to the manager directory and update the npm project:

```bash
git pull
cd manager
npm install
```

## Usage

To run the manager without the service use the following script:

```bash
./manager/manager-run.sh
```

### Service

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

```bash
sudo ./manager/manager-service-uninstall.sh
```

## Credits

Main contribution:
* Martin Fröhlich

Scripts:
* Florian Bruggisser 

