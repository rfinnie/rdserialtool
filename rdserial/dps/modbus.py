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

import pymodbus.client.sync as modsync
import time
import logging

try:
    import bluetooth
    HAS_BLUETOOTH = True
except ImportError:
    HAS_BLUETOOTH = False


class ModbusSerialClient(modsync.ModbusSerialClient):
    pass


class ModbusBluetoothClient(modsync.BaseModbusClient):
    def __init__(self, address, port=1, method='ascii', **kwargs):
        if not HAS_BLUETOOTH:
            raise NotImplementedError('BlueZ not available')

        self.address = address
        self.port = port
        self.method = method
        self.socket = None
        self.baudrate = kwargs.get('baudrate', modsync.Defaults.Baudrate)
        modsync.BaseModbusClient.__init__(self, self.__implementation(method), **kwargs)
        if self.method == 'rtu':
            self._last_frame_end = 0.0
            if self.baudrate > 19200:
                self._silent_interval = 1.75/1000  # ms
            else:
                self._silent_interval = 3.5 * (1 + 8 + 2) / self.baudrate

    @staticmethod
    def __implementation(method):
        method = method.lower()
        if method == 'ascii':
            return modsync.ModbusAsciiFramer(modsync.ClientDecoder())
        elif method == 'rtu':
            return modsync.ModbusRtuFramer(modsync.ClientDecoder())
        elif method == 'binary':
            return modsync.ModbusBinaryFramer(modsync.ClientDecoder())
        elif method == 'socket':
            return modsync.ModbusSocketFramer(modsync.ClientDecoder())
        raise modsync.ParameterException('Invalid framer method requested')

    def connect(self):
        if self.socket:
            return True
        logging.debug('Connecting to {} port {}'.format(self.address, self.port))
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((self.address, self.port))
        if self.method == 'rtu':
            self._last_frame_end = time.time()
        return self.socket is not None

    def close(self):
        if self.socket:
            self.socket.close()
        self.socket = None

    def _send(self, request):
        if not self.socket:
            raise modsync.ConnectionException(self.__str__())
        if not request:
            return 0
        if self.method == 'rtu':
            ts = time.time()
            if ts < self._last_frame_end + self._silent_interval:
                to_sleep = self._last_frame_end + self._silent_interval - ts
                logging.debug('Sleeping {} for 3.5 char @ {} baud ({}) quiet period'.format(
                    to_sleep,
                    self.baudrate,
                    self._silent_interval,
                ))
                time.sleep(to_sleep)

        size = self.socket.send(request)
        if self.method == 'rtu':
            self._last_frame_end = time.time()
        return size

    def _recv(self, size):
        if not self.socket:
            raise modsync.ConnectionException(self.__str__())
        result = self.socket.recv(size)
        if self.method == 'rtu':
            self._last_frame_end = time.time()
        return result

    def __str__(self):
        return '%s:%s' % (self.address, self.port)
