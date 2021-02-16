const telemersion = require("telemersive-bus");
const BusManager = telemersion.BusManager;
const Manager = new BusManager();

Manager.configureServer('telemersion.zhdk.ch', 3883, 3591, 'manager', 'manager', 'tBusManager');
Manager.connectServer();
