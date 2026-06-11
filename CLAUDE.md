# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

*Telemersive Router* is a collection of independent services that let remote *Telemersive Gateway* instances exchange video, audio, and generic data streams (UDP) for telematic performances. The four services are deployed together (typically to `/opt/telemersive-router` on a Debian host with systemd) but are largely standalone codebases in their own subdirectories:

- **switchboard/** — Python/Flask JSON API (`switchboard.py`) that dynamically spawns/kills UDP relay processes ("proxies") on request. This is the core piece of logic in this repo.
- **broker/** — Mosquitto MQTT broker configuration (acl.conf, mosquitto.conf, user list) used as the message bus between manager and gateways.
- **manager/** — Small Node.js service (`busManager.js`) that connects to the broker via the `telemersive-bus` package and bridges bus messages to the switchboard's HTTP API.
- **nat-helper/** — Prebuilt UltraGrid NAT-helper binary + systemd install/uninstall scripts (no source to edit here).

Each subdirectory has its own README.md with installation/configuration details — read those for service-specific deployment instructions.

## Switchboard (core logic)

`switchboard/switchboard.py` is a Flask app exposing a JSON API on port 3591 (configurable via `switchboard-service.cfg`):

- `POST /proxies/` — start a new proxy. Required body fields: `port`, `type`, `room`, `description`. Optional `many_port` (defaults to `port + 1`) for proxy types that need a second socket.
- `GET /proxies/` and `GET /proxies/<port>` — inspect running proxies.
- `DELETE /proxies/<port>` — stop a proxy (idempotent — stopping an already-stopped proxy is not an error).
- `GET /rooms/` and `GET /rooms/<room>` — list proxies grouped by room.

Running proxies are tracked in the in-process `myproxies` dict keyed by port number, each entry holding the proxy object plus its `type`, `desc`, and `room`.

### Proxy types (`switchboard/proxies/`)

Each proxy type is its own module implementing a `multiprocessing.Process` subclass (except `OpenStageControl`, which wraps a `subprocess.Popen`). All proxy classes implement `start()`, `stop()`, and `join()`. New proxy types must be:
1. implemented as a module under `proxies/`,
2. exported from `proxies/__init__.py`,
3. added to `valid_types` in `switchboard.py`, and
4. dispatched in the `if/elif` chain in `start_proxy()`.

Types: `mirror` (echoes packets back, for connectivity testing), `one2oneBi` (1:1 relay), `one2manyMo` (1 source → N sinks, sink→source traffic discarded), `one2manyBi` (1 source ↔ N sinks, uses `many_port` with +1 offset convention), `many2manyBi` (relays to all active clients except sender), `OpenStageControl` (launches an Open Stage Control web UI process; expects a `many2manyBi` proxy already running on `many_port` for OSC relaying).

Proxies that track "active" clients (`one2manyMo`, `one2manyBi`, `many2manyBi`) require clients to send at least one packet per second (a payload-less OSC `/hb` packet is accepted as a heartbeat without being forwarded).

### Manual testing

`switchboard/tests/` contains Pure Data (`.pd`) patches (`test-one2many.pd` and helpers in `tests/include/`) for manually exercising proxy connections — there is no automated test suite.

To run the switchboard locally without installing as a service:
```bash
cd switchboard
python3 switchboard.py
```

## Manager

`manager/busManager.js` configures and connects a `BusManager` from the `telemersive-bus` npm package using credentials from `manager/access.js` (copy from `access.js.template`, gitignored — contains broker URL/port, switchboard port, and broker credentials). Run with `manager/manager-run.sh` (does `npm install` then `node busManager.js`) or `npm install` directly in `manager/`.

## Service install/uninstall scripts

Each service directory (`broker/`, `manager/`, `nat-helper/`, `switchboard/`) has `*-service-install.sh` / `*-service-uninstall.sh` scripts that must be run as root on Debian with systemd — they create system users, install dependencies (and for switchboard, Open Stage Control as a `.deb`), and write `/etc/systemd/system/telemersive-<name>.service` unit files derived from the corresponding `*-service.cfg`. These scripts are deployment tooling, not something to run during normal development.
