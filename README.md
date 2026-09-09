# Telemersive Router

![Diagram](media/TG_ConnectionDiagramDetail.svg)

*Telemersive Router* is a collection of services that allow to connect *Telmersive-Gateways* with each other to exchange video, audio and generic data streams.

## Installation

To install an instance of the *Telemersive Router*, clone the github repository into the installation directory (for example `/opt/telemersive-router`).

```
git clone https://github.com/telemersion/telemersive-router
```

Install and configure the required services in this sequence:

1. the [telemersive-switchboard](./switchboard/README.md).
2. the [telemersive-broker](./broker/README.md).
3. the [telemersive-manager](./manager/README.md).
4. the [telemersive-nathelper](./nat-helper/README.md).

## How it works

[Room lifecycle](./docs/room-lifecycle.md) describes how a room is created,
kept alive and torn down across the manager and the switchboard, how a room's
ports are laid out, and which failure modes the two services can and cannot
detect.

[Debugging a running router](./docs/debugging.md) covers where each service
writes its log — the switchboard's is not in `journalctl` — how to ask a running
switchboard what it is doing, and how to work out why a room lost its media.

## Usage

To manage the services, replace telemersive-XXXX with 

* telemersive-switchboard
* telemersive-broker
* telemersive-manager
* telemersive-nathelper


```bash
# start service
sudo systemctl start telemersive-XXXX.service

# stop service
sudo systemctl stop telemersive-XXXX.service

# restart service
sudo systemctl restart telemersive-XXXX.service

# enable service (auto-start on restart)
sudo systemctl enable telemersive-XXXX.service

# disbale service
sudo systemctl disable telemersive-XXXX.service

# show status
sudo systemctl status telemersive-XXXX.service
```

## Credits

* Roman Haefeli
* Martin Fröhlich
* Florian Bruggisser
* Joel Gähwiler 
