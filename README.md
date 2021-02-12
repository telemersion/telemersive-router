# tpf-switchboard

tpf-switchboard is a service with a JSON API to manage different types
of UDP proxies. UDP proxies are way to establish UDP connections for clients
behind NAT firewalls.



tpf-switchboard is developed in the research project "Spatial Dis-/
Continuities in Telematic Performances". It's one element of our toolset to
enable remote locations to create overlapping spaces on physical and virtual
stages.

## UDP proxy types

Those scripts are intended to be run on a server with a public IP address. They
relay incoming UDP packets between connected clients. We use them to establish
UDP connections between endpoints behind NAT firewalls. 

### mirror

**udp_mirror** mirrors incoming packets. This is useful for testing, for instance
to test if the server port is reachable. Also, it can be used to test applications
like UltraGrid when no second peer is available.

### one2oneBi

**udp_one2oneBi** establishes a connection between two endpoints. As soon as both endpoints
have sent at least one packet, the script starts relaying incoming between clients. This
script handles exactly one connetion with two endpoints.

### one2manyMo

**udp_dyn_proxy** handles many endpoint-to-endpoint connections simultaneously. For
that to work, each client sends a token message with a key word to the server. After
having received the same token message from two different clients, the sever starts
relaying packets between the two clients.

### one2manyBi

**udp_multi_proxy** relays an incoming stream of UDP packets from a source client to
one or many receiving clients. The script opens two listening sockets, one for the
source client and one with an offset for the receiving clients. Receiving clients
need to send a dummy packet in regular intervals to keep their connection alive. 

### many2manyBi
