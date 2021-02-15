# tpf-switchboard

*tpf-switchboard* is a service with a JSON API to manage different types
of UDP proxies. UDP proxies are way to establish UDP connections between
clients from behind NAT firewalls. The UDP proxies support several
connection topologies.

It is written in [Python](https://www.python.org/) and uses the
[flask](https://flask.palletsprojects.com/) framework.

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

**mirror** mirrors incoming packets. This is useful for testing, for instance
to test if the server port is reachable. Also, it can be used to test applications
like UltraGrid when no second peer is available.

**one2oneBi** establishes a connection between two endpoints. As soon as both endpoints
have sent at least one packet, the script starts relaying incoming between clients. This
script handles exactly one connetion with two endpoints.

**one2manyMo** opens two listening socket, a source and a sink. The sink port uses an offset
+1. It relays all incoming traffic from the source to all clients connected to the sink. Sink
clients are requested to send at least one packet per second to signal their active connection.
Packets from sink clients are discarded.

**one2manyBi** establishes 1-to-N connections like **one2manyMo**, but additionally allows
sink clients send packets to the source. The sink port uses an offset of 1. Packets from
source are forwarded to all active sink clients, packets from sink clients are forwarded
to the source client. For keeping connections alive without forwarding any data, **one2manyBi**
discards OSC packets with an address `/hb` and no payload.

**many2manyBi** relays incoming packets to all active clients but to to itself. Clients
are considered active as long as they send at least one packet per second. OSC packets
with an address `/hb` and no payload are discarded and may be used by clients to keep
their connection alive without sending data.


## Deployment

The recommended way of running *tpf-switchboard* is to execute it under
[gunicorn](https://gunicorn.org/). The included script `setup.sh` automates
the process of setting up *tpf-switchboard* as a system service. The script
is tested on *Debian* and *Ubuntu*. Run it as root:

```bash
./setup.sh
```

### Logging
The service logs accesses to `/var/log/tpf-swtichboard/access.log` and other
messages to `/var/log/tpf-switchboard/error.log`.


## About

*tpf-switchboard* is developed in the research project **Spatial Dis-/
Continuities in Telematic Performances**. It is one element of our tool set to
enable remote locations to create overlapping spaces on physical and virtual
stages.

## Authors

  * Roman Haefeli <roman.haefeli@zhdk.ch>

## License

**GPL 3.0** (see [LICENSE.txt](LICENSE.txt))

