# Debugging a running router

Where the services write, what their messages mean, and how to work out why a
room lost its media. For how the pieces fit together, see
[Room lifecycle](./room-lifecycle.md).

## Where each service writes — read this part first

The two services log to different places, and the switchboard's is easy to miss:

| what | where |
| --- | --- |
| manager — rooms, peers, port build commands | `journalctl -u telemersive-manager` |
| switchboard — proxies and relays | `/var/log/telemersive-switchboard/error.log` |
| switchboard — HTTP requests | `/var/log/telemersive-switchboard/access.log` |
| switchboard — service start/stop, killed processes | `journalctl -u telemersive-switchboard` |
| broker | `journalctl -u telemersive-broker` |

**`journalctl -u telemersive-switchboard` does not show what the switchboard is
doing.** Its unit runs gunicorn with `--error-logfile`, so everything the
application and the relays log goes to that file, and the journal holds only
systemd's own entries — the service starting, stopping, and the processes it
killed on the way. A switchboard journal that looks empty during an incident is
normal and means nothing.

So an incident normally needs two logs side by side:

```bash
journalctl -u telemersive-manager --since "10:00" --until "11:00"
sed -n '/Sep  9 10:00/,/Sep  9 11:00/p' /var/log/telemersive-switchboard/error.log
```

## Asking the running system

Often quicker than reading logs. The switchboard answers on port 3591:

```bash
# what is it running, and has it been restarted?
curl -s http://localhost:3591/health

# every proxy of one room, with liveness and traffic counters
curl -s http://localhost:3591/rooms/Taipei-Zurich/state

# one port in detail
curl -s http://localhost:3591/proxies/12002/state
```

`instance` in `/health` changes whenever the switchboard process restarts. If it
differs from what you saw earlier, every proxy was forgotten and rebuilt. `rooms`
gives the proxy count per room — a healthy room has 82.

In a per-proxy state, `running` says whether its process is alive, `revivals`
how often the supervisor had to restart it, and `clients` who is currently
sending. A proxy carrying traffic but showing no clients, or counters that stop
climbing, says the relay is up and the sender is not.

The Gateway (`telemersive-portbay`) polls the same room endpoint every few
seconds and shows it per channel, so a performer noticing dead indicators is
usually the earliest signal that something is wrong.

## A room lost its media

Work down this list; each step distinguishes a different cause.

**1. Is it one channel or the whole room?** One channel points at a single relay
or one peer's settings; the whole room points at the switchboard.

**2. Does the room have all its ports?** `curl -s http://localhost:3591/health`.
Fewer than 82 means some were never created — look in the manager's journal for
`is missing N of 82 ports`, which names them.

**3. Are they running?** `curl -s http://localhost:3591/rooms/<room>/state | grep -c '"running": false'`.
A port that is registered but not running, with `revivals` at the limit, is one
the switchboard tried five times and gave up on. The reason is in `error.log`.

**4. Did the switchboard restart?** Compare `instance` against an earlier value,
or `journalctl -u telemersive-switchboard` for start/stop entries. The manager
notices this by itself within `switchBoardCheckInterval` and rebuilds the ports,
logging `switchboard was restarted`.

**5. Is traffic arriving at all?** If counters in the state endpoint stay at zero
for a relay everyone believes they are sending to, the problem is upstream of the
router — NAT, firewall, or the Gateway sending somewhere else.

## Messages worth recognising

**Switchboard** (`error.log`):

```
[WARNING] Revive proxy: '12042' 'one2manyMo' 'Taipei-Zurich' (attempt 1 of 5)
```
A relay died and was restarted. Once is unremarkable; the same port climbing
towards 5 is a real fault, and the exception that caused it is logged just above.

```
[ERROR]   Error while relaying, recovering (3/10)
[ERROR]   Oops, something went wrong!
```
A relay hit an error and kept going. Reaching 10 in a row ends the process, and
the supervisor then revives it.

```
[WARNING] Could not reach the shared state manager. Client list reporting is now
          disabled for this proxy, packet relaying continues.
```
All relays share one state manager, used only to report their client lists. This
says reporting is off for that relay — **media is unaffected**, but `clients` in
the state endpoint will be empty for it from then on. Many of these at once means
the shared manager died, which is worth investigating even though nothing broke.

```
[WARNING] Switchboard is gone, stopping proxy on 12042
```
The relay noticed its parent had disappeared and shut itself down, rather than
staying behind as an orphan holding the port.

```
[WARNING] Reap proxy:  '12042' 'one2manyMo' 'Taipei-Zurich' (process is gone)
```
A request arrived for a port whose proxy had died; the dead entry was cleared so
the port could be used again.

**Manager** (`journalctl -u telemersive-manager`):

```
  <- switchboard was restarted - it has forgotten the ports of 2 room(s)
        -> room 'Taipei-Zurich' is missing 82 port(s) on the switchboard - sending 82 of them again
        <- restored 82 of 82 port(s) for room Taipei-Zurich
```
Normal recovery after a switchboard restart. `restored 81 of 82` means one port
would not start — the reason is in `error.log`.

```
        <- giving up on port 12900 of room 'Taipei-Zurich' after 3 attempts
```
The manager stopped trying to create a port. Requires a person.

```
    -> peer 'X' not joined anymore - reject from room
```
A peer answered a room ping while no longer on the joined list, usually because
it was evicted moments earlier. Occasional occurrences are normal; a peer stuck
in this state is a Gateway-side problem.

## Reproducing locally

The switchboard runs without being installed as a service, and its tests need
nothing but python3:

```bash
cd switchboard
python3 switchboard.py      # serves on 3591
./tests/run-tests.sh
```

The tests cover the failure modes above — a relay dying, a dead port being
reused, the supervisor reviving one, a relay outliving its parent, and relays
surviving the loss of the shared state manager. Running them against an older
checkout (`./tests/run-tests.sh /path/to/old/switchboard`) is a quick way to
confirm whether a behaviour is a regression.

Note that `python3 switchboard.py` currently only works where `fork` is the
default start method for multiprocessing, which is the case on the Debian hosts
this is deployed to but not on macOS.
