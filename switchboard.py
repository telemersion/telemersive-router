#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tpf-switchboard creates and destroys udp proxies dynamically on request.
"""

import copy
import logging
import sys
import time
import proxies
from flask import Flask, json, Response, request

# format of myproxies
# myproxies = {
#      4484: {
#          'obj': <proxy_obj>,
#          'type': 'simple',
#          'description': 'Some description about the proxy',
#          'room': 'Name of the room'
#      }
# }
myproxies = {}

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
        if key != 'obj':
            r_proxy[key] = proxy[key]
    return r_proxy

def get_proxies_of_room(room):
    proxies_in_room = {}
    for key in myproxies.keys():
        if room == myproxies[key]['room']:
            proxy = representation_format(myproxies[key])
            proxies_in_room[key] = proxy
    return proxies_in_room

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
    try:
        myproxies[proxydef['port']]
    except KeyError:
        try:
            if proxydef['type'] == 'mirror':
                obj = proxies.MirrorProxy(listen_port=proxydef['port'], logger=app.logger)
            elif proxydef['type'] == 'one2oneBi':
                obj = proxies.One2OneBiProxy(listen_port=proxydef['port'], logger=app.logger)
            elif proxydef['type'] == 'one2manyMo':
                obj = proxies.One2ManyMoProxy(listen_port=proxydef['port'], many_port=many_port,
                        logger=app.logger)
            elif proxydef['type'] == 'one2manyBi':
                obj = proxies.One2ManyBiProxy(listen_port=proxydef['port'], many_port=many_port,
                        logger=app.logger)
            elif proxydef['type'] == 'many2manyBi':
                obj = proxies.Many2ManyBiProxy(listen_port=proxydef['port'], logger=app.logger)
            elif proxydef['type'] == 'OpenStageControl':
                obj = proxies.OpenStageControl(http_port=proxydef['port'], many_port=many_port,
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
