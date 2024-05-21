# Telemersive Nat Helper

*nat-helper* contains ultragrids nat-helper.

## Installation

To install the Nat-helper as a service (compiled for Debian Bullseye amd64) use the following command:

```bash
sudo ./nat-helper/nat-helper-service-install.sh
```

## Usage

### Service

```bash
# start service
sudo systemctl start telemersive-nat-helper.service

# stop service
sudo systemctl stop telemersive-nat-helper.service

# restart service
sudo systemctl restart telemersive-nat-helper.service

# enable service (auto-start on restart)
sudo systemctl enable telemersive-nat-helper.service

# disbale service
sudo systemctl disable telemersive-nat-helper.service

# show status
sudo systemctl status telemersive-nat-helper.service
```

## Uninstall

```bash
sudo ./nat-helper/nat-helper-service-uninstall.sh
```

## Credits

Scripts:
* Florian Bruggisser 
