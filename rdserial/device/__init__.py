# rdserialtool
# Copyright (C) 2019-2021 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

import logging

try:
    import bluetooth
    HAS_BLUETOOTH = True
except ImportError:
    HAS_BLUETOOTH = False
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class Serial:
    def __init__(self, port, baudrate=9600):
        if not HAS_SERIAL:
            raise NotImplementedError('pyserial not available')

        self.port = port
        self.baudrate = baudrate
        self.socket = None

    def connect(self):
        if self.socket:
            return True
        logging.debug('Serial: Connecting to {}'.format(self.port))
        self.socket = serial.Serial()
        self.socket.port = self.port
        self.socket.baudrate = self.baudrate
        self.socket.writeTimeout = 0
        self.socket.open()
        return self.socket is not None

    def close(self):
        if self.socket:
            self.socket.close()
        self.socket = None

    def send(self, request):
        if not request:
            return 0
        logging.debug('Serial: SEND begin ({})'.format(request))
        size = self.socket.write(request)
        logging.debug('Serial: SEND end ({} bytes)'.format(size))
        return size

    def recv(self, size):
        result = b''
        logging.debug('Serial: RECV begin')
        while len(result) < size:
            buf = self.socket.read()
            result += buf
        logging.debug('Serial: RECV end ({})'.format(result))
        return result

    def __str__(self):
        return '%s' % self.port


class Bluetooth:
    def __init__(self, address, port=1):
        if not HAS_BLUETOOTH:
            raise NotImplementedError('pybluez not available')

        self.address = address
        self.port = port
        self.socket = None

    def connect(self):
        if self.socket:
            return True
        logging.debug('Bluetooth: Connecting to {} port {}'.format(self.address, self.port))
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((self.address, self.port))
        return self.socket is not None

    def close(self):
        if self.socket:
            self.socket.close()
        self.socket = None

    def send(self, request):
        if not request:
            return 0

        logging.debug('Bluetooth: SEND begin ({})'.format(request))
        size = self.socket.send(request)
        logging.debug('Bluetooth: SEND end ({} bytes)'.format(size))
        return size

    def recv(self, size):
        result = b''
        logging.debug('Bluetooth: RECV begin')
        while len(result) < size:
            buf = self.socket.recv(size)
            result += buf
        logging.debug('Bluetooth: RECV end ({})'.format(result))
        return result

    def __str__(self):
        return '%s:%s' % (self.address, self.port)
