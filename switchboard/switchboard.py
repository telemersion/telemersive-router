#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
telemersive-switchboard creates and destroys udp proxies dynamically on request.
"""

import copy
import logging
import multiprocessing
import sys
import threading
import time
import proxies
from flask import Flask, json, Response, request

# format of myproxies
# myproxies = {
#      4484: {
#          'obj': <proxy_obj>,
#          'state': <ProxyState_obj or None>,
#          'type': 'simple',
#          'description': 'Some description about the proxy',
#          'room': 'Name of the room'
#      }
# }
myproxies = {}

# guards changes to myproxies, which the supervisor thread modifies alongside
# the request handlers. reads take a snapshot instead of the lock, so listing
# proxies is never held up by a proxy that is slow to stop.
myproxies_lock = threading.RLock()

# shared between this process and the proxy processes to expose runtime state
state_manager = multiprocessing.Manager()

# how often the supervisor checks that every registered proxy is still running
supervisor_interval = 5
# how often the supervisor revives the same port before it leaves it alone. a
# proxy that dies immediately every time will not be restarted forever.
max_proxy_revivals = 5

port_range = range(10000, 32768)
baseroute = '/proxies/'
valid_types = ['mirror', 'one2oneBi', 'one2manyMo', 'one2manyBi', 'many2manyBi', 'OpenStageControl']
listen_port = 3591
listen_address = '0.0.0.0'

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.logger.setLevel(logging.INFO)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

class r(Response):
    default_mimetype = 'application/json'

def representation_format(proxy):
    r_proxy = {}
    for key in proxy.keys():
        if key not in ('obj', 'state', 'revivals'):
            r_proxy[key] = proxy[key]
    return r_proxy

def state_format(proxy):
    obj = proxy['obj']
    proxy_state = {
        'running': obj.is_alive(),
        'pid': obj.pid,
        # how often the supervisor had to bring this proxy back
        'revivals': proxy.get('revivals', 0),
    }
    if proxy['state'] is not None:
        proxy_state.update(proxy['state'].to_dict())
    return proxy_state

# the supervisor thread can add or remove entries at any time, so reads work on
# a snapshot rather than iterating myproxies directly
def snapshot():
    return list(myproxies.items())

def rooms_in_use():
    return {proxy['room'] for _port, proxy in snapshot()}

def get_proxies_of_room(room):
    proxies_in_room = {}
    for key, proxy in snapshot():
        if room == proxy['room']:
            proxies_in_room[key] = representation_format(proxy)
    return proxies_in_room

def get_state_of_room(room):
    state_of_room = {}
    for key, proxy in snapshot():
        if room == proxy['room']:
            state_of_room[key] = state_format(proxy)
    return state_of_room

def build_proxy(port, many_port, proxy_type, room):
    """
    Create the proxy object for a definition, along with the shared state it
    reports through. Returns (None, None) for an unknown proxy type.

    Used both when a proxy is requested and when the supervisor revives one, so
    that a revived proxy is built exactly like a freshly requested one.
    """
    state = None
    if proxy_type == 'mirror':
        state = proxies.ProxyState(state_manager, app.logger)
        obj = proxies.MirrorProxy(listen_port=port, logger=app.logger, state=state)
    elif proxy_type == 'one2oneBi':
        state = proxies.ProxyState(state_manager, app.logger)
        obj = proxies.One2OneBiProxy(listen_port=port, logger=app.logger, state=state)
    elif proxy_type == 'one2manyMo':
        state = proxies.ProxyState(state_manager, app.logger)
        obj = proxies.One2ManyMoProxy(listen_port=port, many_port=many_port,
                logger=app.logger, state=state)
    elif proxy_type == 'one2manyBi':
        state = proxies.ProxyState(state_manager, app.logger)
        obj = proxies.One2ManyBiProxy(listen_port=port, many_port=many_port,
                logger=app.logger, state=state)
    elif proxy_type == 'many2manyBi':
        state = proxies.ProxyState(state_manager, app.logger)
        obj = proxies.Many2ManyBiProxy(listen_port=port, logger=app.logger, state=state)
    elif proxy_type == 'OpenStageControl':
        obj = proxies.OpenStageControl(http_port=port, osc_port=many_port,
                session=room, logger=app.logger)
    else:
        return None, None
    return obj, state

def release_sockets(obj):
    """
    Close a proxy's sockets in this process.

    Proxy sockets are opened in the proxy's __init__, which runs here in the
    switchboard - the relay process only inherits them across the fork. So when
    a relay exits, its port stays bound by our own copy of the socket until the
    object happens to be garbage collected. Closing explicitly makes releasing
    the port deterministic instead of depending on refcount timing.
    """
    for name in ('sock', 'source', 'sink'):
        sock = getattr(obj, name, None)
        if sock is None:
            continue
        try:
            sock.close()
        except Exception:
            app.logger.exception("Could not close '%s' socket", name)

def reap_dead_proxy(port):
    """
    Drop the bookkeeping entry of a proxy whose process is gone.

    An entry in myproxies only records that a proxy was started once, it says
    nothing about whether it is still running. Without reaping, a proxy that
    died would keep answering 'already running' for its own port and could
    never be replaced - the port would stay dead until the whole room is torn
    down and recreated, which needs every peer to leave the room first.
    """
    proxy = myproxies.get(port)
    if proxy is None or proxy['obj'].is_alive():
        return False
    app.logger.warning("Reap proxy:  '%s' '%s' '%s' (process is gone)",
            port, proxy['type'], proxy['room'])
    try:
        proxy['obj'].join()
    except Exception:
        app.logger.exception('Could not join dead proxy on port %s', port)
    release_sockets(proxy['obj'])
    del myproxies[port]
    return True

def revive_dead_proxies():
    """
    Restart the proxies whose process is no longer running.

    Nothing else notices when a relay dies: the telemersive-manager tracks peer
    liveness over MQTT, not the media path, and it only creates ports for a room
    that does not exist yet - so a room that outlives its proxies would keep its
    ports dead until every peer has left it. A revived proxy binds its port
    again and the peers re-register with it on their next packet.
    """
    revived = []
    with myproxies_lock:
        for port, proxy in list(myproxies.items()):
            if proxy['obj'].is_alive():
                continue
            if proxy.get('revivals', 0) >= max_proxy_revivals:
                continue
            proxy['revivals'] = proxy.get('revivals', 0) + 1
            attempt = proxy['revivals']
            app.logger.warning("Revive proxy: '%s' '%s' '%s' (attempt %s of %s)",
                    port, proxy['type'], proxy['room'], attempt, max_proxy_revivals)
            try:
                proxy['obj'].join()
            except Exception:
                app.logger.exception('Could not join dead proxy on port %s', port)
            release_sockets(proxy['obj'])
            try:
                obj, state = build_proxy(port, proxy['sink-port'], proxy['type'],
                        proxy['room'])
                if obj is None:
                    raise ValueError(f"unknown proxy type '{proxy['type']}'")
                obj.start()
            except Exception:
                # keep the entry so the next pass can try again, up to the limit
                app.logger.exception('Could not revive proxy on port %s', port)
                continue
            proxy['obj'] = obj
            proxy['state'] = state
            revived.append(port)
    return revived

def supervise_proxies():
    while True:
        time.sleep(supervisor_interval)
        try:
            revive_dead_proxies()
        except Exception:
            # the supervisor must outlive any single failed pass
            app.logger.exception('Supervisor pass failed')

def start_supervisor():
    supervisor = threading.Thread(target=supervise_proxies, name='proxy-supervisor',
            daemon=True)
    supervisor.start()
    return supervisor

@app.route(baseroute, methods=['POST'])
def start_proxy():
    proxydef = request.get_json()
    # Do some input sanitizing
    # port
    try:
        assert proxydef['port'] in port_range
        assert isinstance(proxydef['port'], int)
    except AssertionError:
        response = {'status': 'Error', 'msg': 'Allowed port range is %s - %s' % (min(port_range), max(port_range))}
        return r(json.dumps(response), 422)
    except KeyError:
        response = {'status': 'Error', 'msg': 'No port specified'}
        return r(json.dumps(response), 422)
    # many_port is not mandatory for all proxies
    many_port = proxydef['port'] + 1
    if 'many_port' in proxydef:
        try:
            assert proxydef['many_port'] in port_range
            assert isinstance(proxydef['many_port'], int)
        except AssertionError:
            response = {'status': 'Error', 'msg': 'Allowed many_port range is %s - %s' % (min(port_range), max(port_range))}
            return r(json.dumps(response), 422)
        except KeyError:
            response = {'status': 'Error', 'msg': 'No many_port specified'}
            return r(json.dumps(response), 422)
        many_port = proxydef['many_port']
    # type
    try:
        assert proxydef['type'] in valid_types
        assert isinstance(proxydef['type'], str)
    except AssertionError:
        response = {'status': 'Error', 'msg': 'Invalid type specified: %s' % proxydef['type']}
        return r(json.dumps(response), 422)
    except KeyError:
        response = {'status': 'Error', 'msg': 'No type specified'}
        return r(json.dumps(response), 422)
    # description
    try:
        assert isinstance(proxydef['description'], str)
    except AssertionError:
        response = {'status': 'Error', 'msg': 'Invalid description specified'}
        return r(json.dumps(response), 422)
    except KeyError:
        response = {'status': 'Error', 'msg': 'No description specified'}
        return r(json.dumps(response), 422)
    # room
    try:
        assert isinstance(proxydef['room'], str)
    except AssertionError:
        response = {'status': 'Error', 'msg': 'Invalid room specified'}
        return r(json.dumps(response), 422)
    except KeyError:
        response = {'status': 'Error', 'msg': 'No room specified'}
        return r(json.dumps(response), 422)
    # Done input sanitizing
    with myproxies_lock:
        # if a proxy previously started on this port has died, clear it out
        # first so this request can replace it instead of being rejected by its
        # corpse.
        reap_dead_proxy(proxydef['port'])
        if proxydef['port'] in myproxies:
            response = {'status': 'Error', 'msg': 'Proxy already running on port %s' % proxydef['port']}
            return r(json.dumps(response), 422)
        try:
            obj, state = build_proxy(proxydef['port'], many_port,
                    proxydef['type'], proxydef['room'])
        except OSError as err:
            response = {'status': 'Error', 'msg': str(err)}
            return r(json.dumps(response), 422)
        if obj is None:
            response = {'status': 'Error', 'msg': 'An unknown error occurred'}
            return r(json.dumps(response), 422)
        obj.start()
        myproxies[proxydef['port']] = {
            'obj': obj,
            'state': state,
            'source-port': proxydef['port'],
            'sink-port': many_port,
            'type': proxydef['type'],
            'desc': proxydef['description'],
            'room': proxydef['room'],
            'revivals': 0
        }
        response = {'status': 'OK', 'msg': 'Proxy successfully started'}
        app.logger.info("Start proxy: '%s' '%s' '%s'", proxydef['port'], proxydef['type'], proxydef['room'])
        return r(json.dumps(response), 201)

@app.route(baseroute + '<int:port>', methods=['DELETE'])
def stop_proxy(port):
    with myproxies_lock:
        try:
            myproxies[port]['obj'].stop()
            myproxies[port]['obj'].join()
            app.logger.info("Stop proxy:  '%s' '%s' '%s'", port, myproxies[port]['type'], myproxies[port]['room'])
            release_sockets(myproxies[port]['obj'])
            del myproxies[port]
            response = {'status': 'OK', 'msg': 'Proxy successfully stopped'}
            return r(json.dumps(response))
        except KeyError:
            response = {'status': 'OK', 'msg': 'Proxy is not running'}
            return r(json.dumps(response))

@app.route(baseroute, methods=['GET'])
def list_proxies():
    proxies = {}
    for key, proxy in snapshot():
        proxies[key] = representation_format(proxy)
    return r(json.dumps(proxies))

@app.route(baseroute + '<int:port>', methods=['GET'])
def get_proxy(port):
    try:
        proxy = representation_format(myproxies[port])
        return r(json.dumps(proxy))
    except KeyError:
        return r(json.dumps({'status': 'Error', 'msg': 'No proxy running on this port'}), 404)

@app.route(baseroute + '<int:port>/state', methods=['GET'])
def get_proxy_state(port):
    try:
        return r(json.dumps(state_format(myproxies[port])))
    except KeyError:
        return r(json.dumps({'status': 'Error', 'msg': 'No proxy running on this port'}), 404)

@app.route('/rooms/', methods=['GET'])
def get_proxies_grouped_by_room():
    all_rooms = {}
    for room in rooms_in_use():
        proxies_of_room = get_proxies_of_room(room)
        all_rooms[room] = proxies_of_room
    return r(json.dumps(all_rooms))

@app.route('/rooms/' + '<string:room>', methods=['GET'])
def get_proxies_of_room_http(room):
    try:
        assert room in rooms_in_use()
    except AssertionError:
        response = {'status': 'Error', 'msg': 'No such room found: %s' % room}
        return r(json.dumps(response), 404)
    proxies_of_room = get_proxies_of_room(room)
    return r(json.dumps(proxies_of_room))

@app.route('/rooms/' + '<string:room>/state', methods=['GET'])
def get_state_of_room_http(room):
    try:
        assert room in rooms_in_use()
    except AssertionError:
        response = {'status': 'Error', 'msg': 'No such room found: %s' % room}
        return r(json.dumps(response), 404)
    return r(json.dumps(get_state_of_room(room)))

# started on import so it also runs under gunicorn, which imports this module in
# the worker that owns the proxies
start_supervisor()

def main():
    try:
        app.run(host=listen_address, port=listen_port)
    except KeyboardInterrupt:
        for _port, proxy in snapshot():
            proxy['obj'].stop()
            proxy['obj'].join()
        sys.exit(0)

if __name__ == '__main__':
    main()
