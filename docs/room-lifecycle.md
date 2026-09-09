# Room lifecycle

How a room comes into existence, stays alive, and is torn down across the
*manager* and the *switchboard* — and which parts of that are load bearing when
something goes wrong.

The room logic itself does not live in this repository: the manager is a thin
wrapper ([`manager/busManager.js`](../manager/busManager.js)) around the
`telemersive-bus` npm package, and all the behaviour described here comes from
that package's `lib/BusManager.js`.

## Two services, two views of the world

The two services keep entirely separate state, connected only by HTTP. The
manager decides what should exist; the switchboard decides whether what exists
is healthy.

```
  Gateway peers
       │  MQTT (mosquitto broker)
       ▼
  ┌─────────────────────┐   POST / DELETE →    ┌──────────────────────┐
  │  manager            │ ───────────────────► │  switchboard         │
  │  (telemersive-bus)  │ ◄─────────────────── │  (Flask/gunicorn)    │
  │                     │    ← GET /health     │                      │
  │  this.rooms{}       │                      │  myproxies{}         │
  │  which rooms exist  │                      │  which ports are     │
  │  and who joined     │                      │  registered          │
  └─────────────────────┘                      └──────────────────────┘
                                                    │ forks one process
                                                    ▼ per proxy
                                            relay processes (UDP)
                                                    ▲
  Gateway peers ────────────────────────────────────┘
       audio / video / data — never passes through the manager
```

The media path never touches the manager. Peers send UDP straight at the
switchboard's relay processes; the manager only does signalling.

## Ports of a room

Each room gets an id between 11 and 49 (`ROOM_ID_MIN`/`ROOM_ID_MAX`, assigned by
`findUnusedRoomId`) and owns the port block `id*1000 … id*1000+999`. Room 12
therefore lives on 12000–12999.

`startServerSidePortScripts` creates **82 proxies** per room — 20 channels of
four, plus two for Open Stage Control:

| what | port | many_port | type |
| --- | --- | --- | --- |
| OSC, channel *i* | `id*1000 + i*10 + 9` | same | `many2manyBi` |
| UltraGrid video, channel *i* | `id*1000 + i*10 + 2` | `+6` | `one2manyMo` |
| UltraGrid audio / NatNet data, channel *i* | `id*1000 + i*10 + 4` | `+8` | `one2manyMo` |
| MoCap / NatNet control, channel *i* | `id*1000 + i*10 + 0` | `+1` | `one2manyBi` |
| Open Stage Control relay | `id*1000 + 902` | same | `many2manyBi` |
| Open Stage Control UI | `id*1000 + 900` | `id*1000 + 902` | `OpenStageControl` |

Each `POST /proxies/` is sent and awaited individually, and a room is never
rolled back if some of them fail — it simply comes up with fewer ports than it
should. Failed calls are retried once at creation, and anything still missing is
named in the log and picked up again by the health check below.

## Birth

1. A peer asks for a room that does not exist, or a retained room message
   arrives after a manager restart (`onRooms`).
2. `createNewRoom` assigns the lowest free room id, stores the room in
   `this.rooms`, and starts a `ChatManager` for it.
3. `startServerSidePortScripts` POSTs all 82 proxies to the switchboard.
4. Each POST forks a relay process and registers it in `myproxies[port]`.

## Steady state

Four liveness mechanisms run side by side, each measuring something different.

**Peer liveness — manager, over MQTT.** A kill list, rebuilt from scratch every
cycle. `startHousekeeping` clears `peerHousekeep`, subscribes to the retained
join messages to repopulate it, waits, pings every room, waits again, then
`cleanOut` evicts whoever is *still on the list*. Answering a ping is how a peer
gets **removed** from it, and a single answer also rescues the whole room from
`roomHousekeep`. A cycle is started at boot, on peer join (after 5s) and on peer
leave (after 1s); its phases are 1.5s apart. Self-correcting.

**Client liveness — switchboard, over UDP.** Every relay tracks its own senders
by the time of their last packet and forgets them after 10s of silence. Gateways
send heartbeats well inside that window; a payload-less OSC `/hb` packet counts
as a heartbeat without being forwarded. Self-correcting.

**Switchboard liveness — the manager, on its own timer.** Every
`switchBoardCheckInterval` the manager reads `GET /health`. A changed `instance`
means the switchboard restarted and forgot everything; a room holding fewer
proxies than it should means some were never created. Either way the manager
re-sends only the ports the switchboard does not have. This deliberately does
not run inside housekeeping, which only fires on peer join and leave and can go
an hour without a cycle while a performance is under way.

**Proxy liveness — the switchboard's own supervisor.** A background thread
checks every `supervisor_interval` seconds that each registered proxy is still
running and restarts the ones that are not, up to `max_proxy_revivals` times per
port so a proxy that cannot survive is not restarted forever. A revived proxy
binds its port again and the peers re-register with it on their next packet.
`GET /proxies/<port>/state` reports `revivals` alongside `running` and `pid`.

Note what the manager deliberately does *not* look at: whether a proxy is
running. It reads only which ports the switchboard holds. Health is the
switchboard's to judge and to act on — see the table at the end.

## Death

When no peer answers a room's ping for a full cycle, the room is still in
`roomHousekeep` at `cleanOut` and gets deleted:

1. `deleteRoom` → `stopServerSidePortScripts`
2. `DELETE /proxies/<port>` for all 82 ports
3. a 3s settle (`proxyShutdownSettleTime`) so the OS can release the ports
4. the room is removed from `this.rooms`

## Failure modes

**A relay process dies while the room lives on.** Peer liveness keeps reporting
the room as perfectly healthy, because it is measuring MQTT traffic, not the
media path. The room is never rebuilt, so the dead port stays dead. Recovery
used to require every peer to leave so the room could be torn down and
recreated — not an option mid-performance.

Three things now prevent this from becoming permanent:

- Relays survive transient errors. A failed loop iteration is logged and
  retried rather than ending the process, and only `MAX_CONSECUTIVE_ERRORS`
  failures in a row will end a relay
  ([`proxies/state.py`](../switchboard/proxies/state.py)).
- A dead proxy no longer blocks its own port. `start_proxy` reaps an entry
  whose process is gone and recreates it, so any repeated POST for that port
  repairs it. Previously the stale entry answered `Proxy already running`,
  which is a statement about registration, not about liveness.
- The supervisor restarts a proxy that died without anyone having to ask,
  which is what makes recovery possible while the room is still in use.

**The shared state manager becomes unreachable.** All proxies of all rooms
share one `multiprocessing.Manager()` ([`switchboard.py`](../switchboard/switchboard.py)),
used only to publish each relay's client list. It is a single point of failure
that reaches every room at once, so reporting through it is treated as
optional: if it cannot be reached, the relay logs once, switches reporting off
and keeps forwarding packets. Relaying itself needs nothing from it — the
packet counters are plain shared memory.

**Socket ownership.** A proxy's sockets are opened in its `__init__`, which runs
in the switchboard process; the relay process only inherits them across the
fork. A port therefore stays bound by the switchboard's own copy after the relay
exits, until that object is garbage collected. `release_sockets` closes them
explicitly on both teardown paths so releasing a port does not depend on
refcount timing.

**Restarting the switchboard drops every room.** `myproxies` is in-process
memory with no persistence, and relay processes live in the service's cgroup.
Restarting `telemersive-switchboard` kills every relay of every room instantly,
and the manager will not rebuild them for any room that still exists (see
above). Avoid restarting it while rooms are live.

**Open Stage Control sessions.** Each room gets a session directory named after
the room. Room names are chosen by the clients and are not restricted, so they
are reduced to safe characters before being used as a path — a name containing
`..` or `/` would otherwise escape the sessions directory, and one containing
shell metacharacters used to be interpreted as a command, because the session
template was copied with `os.system`. It is copied directly now.

**The switchboard is restarted while rooms are live.** Every relay dies with it
and `myproxies` comes back empty, while the rooms themselves carry on: peers
keep answering their pings, no room is torn down, and nothing would ask for the
ports again. The manager therefore polls `GET /health` on its own timer, and
when the `instance` it sees differs from the one before — or a room holds fewer
proxies than it should — it sends the build commands for the missing ports
again. Restarting the switchboard mid-session is now a gap of seconds rather
than something that lasts until every peer has left.

## Who repairs what

Each failure mode has exactly one owner, which is what keeps the two services
from undoing each other:

| failure | noticed by | repaired by |
| --- | --- | --- |
| a relay dies | switchboard supervisor | switchboard, up to `max_proxy_revivals` |
| a relay cannot be kept alive | switchboard, after giving up | nobody — reported as `running: false` for a person to act on |
| a `POST` failed at room creation | manager, from the failed call | manager, retried immediately |
| the switchboard was restarted | manager, from `instance` | manager, re-sends the room's build commands |

The rule underneath the table: **the manager only ever sends ports the
switchboard does not have.** A port it holds but is not running is the
switchboard's business, including its decision to stop trying. Re-sending such a
port would reap the entry and reset its revival count, and the two services
would restart the same broken proxy forever.
