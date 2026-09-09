#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
telemersive-switchboard creates and destroys udp proxies dynamically on request.
"""

import copy
import logging
import multiprocessing
import sys
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

# shared between this process and the proxy processes to expose runtime state
state_manager = multiprocessing.Manager()

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
        if key not in ('obj', 'state'):
            r_proxy[key] = proxy[key]
    return r_proxy

def state_format(proxy):
    obj = proxy['obj']
    proxy_state = {
        'running': obj.is_alive(),
        'pid': obj.pid,
    }
    if proxy['state'] is not None:
        proxy_state.update(proxy['state'].to_dict())
    return proxy_state

def get_proxies_of_room(room):
    proxies_in_room = {}
    for key in myproxies.keys():
        if room == myproxies[key]['room']:
            proxy = representation_format(myproxies[key])
            proxies_in_room[key] = proxy
    return proxies_in_room

def get_state_of_room(room):
    state_of_room = {}
    for key in myproxies.keys():
        if room == myproxies[key]['room']:
            state_of_room[key] = state_format(myproxies[key])
    return state_of_room

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
    # if a proxy previously started on this port has died, clear it out first so
    # this request can replace it instead of being rejected by its corpse.
    reap_dead_proxy(proxydef['port'])
    try:
        myproxies[proxydef['port']]
    except KeyError:
        state = None
        try:
            if proxydef['type'] == 'mirror':
                state = proxies.ProxyState(state_manager, app.logger)
                obj = proxies.MirrorProxy(listen_port=proxydef['port'], logger=app.logger, state=state)
            elif proxydef['type'] == 'one2oneBi':
                state = proxies.ProxyState(state_manager, app.logger)
                obj = proxies.One2OneBiProxy(listen_port=proxydef['port'], logger=app.logger, state=state)
            elif proxydef['type'] == 'one2manyMo':
                state = proxies.ProxyState(state_manager, app.logger)
                obj = proxies.One2ManyMoProxy(listen_port=proxydef['port'], many_port=many_port,
                        logger=app.logger, state=state)
            elif proxydef['type'] == 'one2manyBi':
                state = proxies.ProxyState(state_manager, app.logger)
                obj = proxies.One2ManyBiProxy(listen_port=proxydef['port'], many_port=many_port,
                        logger=app.logger, state=state)
            elif proxydef['type'] == 'many2manyBi':
                state = proxies.ProxyState(state_manager, app.logger)
                obj = proxies.Many2ManyBiProxy(listen_port=proxydef['port'], logger=app.logger, state=state)
            elif proxydef['type'] == 'OpenStageControl':
                obj = proxies.OpenStageControl(http_port=proxydef['port'], osc_port=many_port,
                        session=proxydef['room'], logger=app.logger)
            else:
                response = {'status': 'Error', 'msg': 'An unknown error occurred'}
                return r(json.dumps(response), 422)
        except OSError as err:
            response = {'status': 'Error', 'msg': str(err)}
            return r(json.dumps(response), 422)
        else:
            obj.start()
            myproxies[proxydef['port']] = {
                'obj': obj,
                'state': state,
                'source-port': proxydef['port'],
                'sink-port': many_port,
                'type': proxydef['type'],
                'desc': proxydef['description'],
                'room': proxydef['room']
            }
            response = {'status': 'OK', 'msg': 'Proxy successfully started'}
            app.logger.info("Start proxy: '%s' '%s' '%s'", proxydef['port'], proxydef['type'], proxydef['room'])
            return r(json.dumps(response), 201)
    else:
        response = {'status': 'Error', 'msg': 'Proxy already running on port %s' % proxydef['port']}
        return r(json.dumps(response), 422)

@app.route(baseroute + '<int:port>', methods=['DELETE'])
def stop_proxy(port):
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
    for key in myproxies.keys():
        proxies[key] = representation_format(myproxies[key])
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
    rooms = {myproxies[key]['room'] for key in myproxies.keys()}
    all_rooms = {}
    for room in rooms:
        proxies_of_room = get_proxies_of_room(room)
        all_rooms[room] = proxies_of_room
    return r(json.dumps(all_rooms))

@app.route('/rooms/' + '<string:room>', methods=['GET'])
def get_proxies_of_room_http(room):
    try:
        assert room in {myproxies[key]['room'] for key in myproxies.keys()}
    except AssertionError:
        response = {'status': 'Error', 'msg': 'No such room found: %s' % room}
        return r(json.dumps(response), 404)
    proxies_of_room = get_proxies_of_room(room)
    return r(json.dumps(proxies_of_room))

@app.route('/rooms/' + '<string:room>/state', methods=['GET'])
def get_state_of_room_http(room):
    try:
        assert room in {myproxies[key]['room'] for key in myproxies.keys()}
    except AssertionError:
        response = {'status': 'Error', 'msg': 'No such room found: %s' % room}
        return r(json.dumps(response), 404)
    return r(json.dumps(get_state_of_room(room)))

def main():
    try:
        app.run(host=listen_address, port=listen_port)
    except KeyboardInterrupt:
        for port in myproxies.keys():
            myproxies[port]['obj'].stop()
            myproxies[port]['obj'].join()
        sys.exit(0)

if __name__ == '__main__':
    main()
