# rdserialtool
# Copyright (C) 2019 Ryan Finnie
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

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


class Bluetooth:
    dev = None

    def __init__(self, address, port=1):
        if not HAS_BLUETOOTH:
            raise NotImplementedError('BlueZ not available')

        self.address = address
        self.port = port

    def connect(self):
        logging.debug('CONNECT')
        self.dev = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.dev.connect((self.address, self.port))

    def close(self):
        if self.dev is None:
            return
        logging.debug('CLOSE')
        self.dev.close()
        self.dev = None

    def send(self, data):
        logging.debug('SEND: {}'.format(repr(data)))
        self.dev.send(data)

    def recv(self):
        data = b''
        while(len(data) < 130):
            data += self.dev.recv(1024)
        logging.debug('RECV: {}'.format(repr(data)))
        return data


class Serial:
    dev = None

    def __init__(self, device, baudrate=9600):
        if not HAS_SERIAL:
            raise NotImplementedError('pyserial not available')

        self.device = device
        self.baudrate = baudrate

    def connect(self):
        logging.debug('CONNECT')
        self.dev = serial.Serial()
        self.dev.port = self.device
        self.dev.baudrate = self.baudrate
        self.dev.writeTimeout = 0
        self.dev.open()

    def close(self):
        if self.dev is None:
            return
        logging.debug('CLOSE')
        self.dev.close()
        self.dev = None

    def send(self, data):
        logging.debug('SEND: {}'.format(repr(data)))
        self.dev.write(data)

    def recv(self):
        data = b''
        while(len(data) < 130):
            data += self.dev.read()
        logging.debug('RECV: {}'.format(repr(data)))
        return data
