var access = require('./access');
const telemersion = require("telemersive-bus");
const BusManager = telemersion.BusManager;
const Manager = new BusManager();

Manager.configureServer(access.broker_url, access.broker_port, access.switch_port, access.user, access.pwd, 'tBusManager');
Manager.connectServer();
