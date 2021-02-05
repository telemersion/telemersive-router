#!/usr/bin/env python3

from flask import Flask, json, Response, request

myproxies = {
    11010: {
        'port': 11010,
        'type': 'one2oneBi',
        'description': 'UltraGrid Kamera Bühne'
    },
    11015: {
        'port': 11015,
        'type': 'one2manyMo',
        'description': 'OSC / MoCap Konzertsaal 1'
    }
}

api = Flask(__name__)

baseroute = '/proxies/'

class r(Response):
    default_mimetype = 'application/json'

@api.route(baseroute + '<int:port>', methods=['GET'])
def get_proxy(port):
    try:
        return r(json.dumps(myproxies[port]))
    except KeyError:
        return r(json.dumps({'status': 'Error', 'msg': 'No proxy running on this port'}), 404)

@api.route(baseroute, methods=['GET'])
def list_proxies():
    return r(json.dumps(myproxies))

@api.route(baseroute, methods=['POST'])
def start_proxy():
    data = request.get_json()
    myproxies[data['port']] = data
    response = {'status': 'OK', 'msg': 'Proxy successfully created'}
    return r(json.dumps(response), 201)

@api.route(baseroute + '<int:port>', methods=['DELETE'])
def stop_proxy(port):
    try:
        del myproxies[port]
        response = {'status': 'OK', 'msg': 'Proxy successfully stopped'}
        return r(json.dumps(response))
    except KeyError:
        response = {'status': 'OK', 'msg': 'Proxy is not running'}
        return r(json.dumps(response))

if __name__ == '__main__':
    api.run(host='0.0.0.0', port=8080)

