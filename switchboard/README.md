# Telemersive Switchboard

*Telemersive Switchboard* is developed in the research project **Spatial Dis-/Continuities in Telematic Performances**. It is one element of our tool set to enable remote locations to create overlapping spaces on physical and virtualstages.

*Telemersive Switchboard* is a service with a JSON API to manage different types of UDP proxies. UDP proxies are way to establish UDP connections between clients from behind NAT firewalls. The UDP proxies support several
connection topologies.

It is written in [Python](https://www.python.org/) and uses the
[flask](https://flask.palletsprojects.com/) framework.


## Requirement

### Installing OpenStageControl

[OpenStageControl](https://openstagecontrol.ammd.net/) is a web application that allows the easy creation of user interfaces and is seamlessly integrated in the telemersive toolkit:

```bash
sudo apt install gdebi-core wget
wget "https://github.com/jean-emmanuel/open-stage-control/releases/download/v1.26.2/open-stage-control_1.26.2_amd64.deb"
sudo gdebi open-stage-control_1.26.2_amd64.deb
```

### Setup OpenStageControl for instantiating by switchboard

When an instance of the `OpenStageControl` module is started, it automatically creates a folder named after the room and copies
a default session to that new folder. Thus, we need to make sure the folder exists and the user OpenStageControl runs under has
access to it:

```bash
sudo mkdir -p /opt/open-stage-control/sessions/tsb_sessions
sudo chown -R telemersive-switchboard:telemersive-switchboard /opt/open-stage-control/sessions
```

We also need to create a template session that is automatically loaded in a new room and save it under this path:  

```bash
/opt/open-stage-control/sessions/tsb_sessions/template.json
```

## Installation

To install the switchboard as a service (Debian with systemd) use the following command:

```bash
cd switchboard
./switchboard-service-install.sh
```

The recommended way of running *Telemersive Switchboard* is to execute it under [gunicorn](https://gunicorn.org/). The included script `setup.sh` automates the process of setting up Telemersive Switchboard* as a system service. The script is tested on *Debian* and *Ubuntu*. Run it as root:

## Configuration

### Restrict Accessibility

```bash
# TBD
```

## Usage

### Service

```bash
# start service
sudo systemctl start telemersive-switchboard.service

# stop service
sudo systemctl stop telemersive-switchboard.service

# restart service
sudo systemctl restart telemersive-switchboard.service

# enable service (auto-start on restart)
sudo systemctl enable telemersive-switchboard.service

# disbale service
sudo systemctl disable telemersive-switchboard.service

# show status
sudo systemctl status telemersive-switchboard.service
```

### Logging
The service logs accesses to `/var/log/telemersive-swtichboard/access.log` and other messages to `/var/log/telemersive-switchboard/error.log`.

## Uninstall

```bash
sudo ./switchboard/switchboard-service-uninstall.sh.sh
```

## JSON API description

### Start a new proxy

A new proxy process is launched by sending a HTTP `POST` request with POST data
containing the description of the new proxy in JSON format to the path `<base>/proxies/`.
An example of POST data:

```json
{
    "port": 11000,
    "type", "one2oneBi",
    "room": "rehearsal",
    "description": "UltraGrid stage"
}
```

All four parameters `port`, `type`, `room`, and `description` are mandatory and must
be specified. Omitting any of them causes an error.

cURL example for starting a new proxy:

```bash
curl \
  --header "Content-Type: application/json" \
  --request POST \
  --data '{"port": 11000, "type": "one2oneBi", "description": "UltraGrid stage", "room": "rehearsal"}' \
  http://localhost:3591/proxies/
```

### Inspect running proxies

#### path `<base>/proxies/`

Information about running proxies is gathered with a HTTP `GET` request to `<base>/proxies/`. For
a specific proxy, use the proxy's specific path `<base>/proxies/<port>`.

cURL examples:

```bash
curl \
  --requeset GET \
  http://localhost:3591/proxies/
```

```bash
curl \
  --requeset GET \
  http://localhost:3591/proxies/11000
```

#### path `<base>/rooms/`

You can also request running proxies grouped by room through `<base>/rooms/`. Also, all
proxies running in a specific room can be listed.

cURL examples:

```bash
curl \
  --request GET \
  http://localhost:3591/rooms/
```

```bash
curl \
  --request GET \
  http://localhost:3591/rooms/rehearsal
```

### Stop a running proxy

A running proxy is stopped with a HTTP `DELETE` request to the proxy's path.

cURL example:

```bash
curl \
  --request DELETE \
   http://localhost:3591/proxies/11000
```

**NOTE**:  
Since `DELETE` requests should be treated in an idem-potent way, stopping
an already stopped proxy is considered not an error.

### Return values

For requests to semantically valid paths, the return value is a JSON object
of the format:

```json
{
  "status": "<Either 'Error' or 'OK'>",
  "msg": "<Some message describing the status>"
}
```

Depending on type of request and on status, different HTTP status codes are
returned. HTTP status may be one of `200`, `201`, `404`, `422`.


## UDP proxy types

**mirror** mirrors incoming packets. This is useful for testing, for instance to test if the server port is reachable. Also, it can be used to test applications like UltraGrid when no second peer is available.

**one2oneBi** establishes a connection between two endpoints. As soon as both endpoints have sent at least one packet, the script starts relaying incoming between clients. This script handles exactly one connection with two endpoints.

**one2manyMo** establishes 1-to-N connections and opens two listening socket, a source and a sink. The sink port uses an offset of
+1. It relays all incoming traffic from the source to all clients connected to the sink. Sink clients are requested to send at least one packet per second to indicate their active connection.
Packets from sink clients are discarded.

**one2manyBi** establishes 1-to-N connections like **one2manyMo**, but additionally allows
sink clients to send packets to the source. The sink port uses an offset of +1. Packets from
source client are forwarded to all active sink clients, packets from sink clients are forwarded
to the source client. Source AND Sink
clients are requested to send at least one packet per second to indicate their active connection.

**many2manyBi** relays incoming packets to all active clients but to to itself. Clients
are considered active as long as they send at least one packet per second.

**OpenStageControl** is not a proxy module, but starts and stops an instance of an [Open Stage Control](https://openstagecontrol.ammd.net/docs/getting-started/introduction/) server. `port` specifies the listening port for the webserver, `many_port` specifies the destination UDP port for OSC messages. See section below for more detailed documentation about setting up and using OpenStageControl.

#### Note
**one2manyMo**, **one2manyBi** and **many2manyBi**
On ports that require packets to indicate an active connection, these scripts also accept an OSC packet without a payload and the address `/hb` without forwarding this packet.

### Interaction between OpenStageControl and OSC clients

By the use of a `many2manyBi` proxy, we can send OSC events generated in OpenStageControl to many OSC clients. In return,
many OSC clients can send OSC messages to OpenStageControl. telemersive-switchboard does not autamically start a `many2manyBi`
proxy when launching an instance of `OpenStageControl`. For this to work, `port` of `many2manyBi` must be set to `many_port`
of `OpenStageControl`. The telemersive-gateway automatically sets up a proxy for OSC message relaying when starting an
instance of `OpenStageControl`.

## Credits

Main contribution:
* Roman Haefeli 

Programming:
* Martin Froehlich 
* Florian Bruggisser 

Bug Fixing:
* Joel Gähwiler 

