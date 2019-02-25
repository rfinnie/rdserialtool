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

# Note that is a massively simplified Modbus RTU client,
# and is not suitable for general Modbus use.

import time
import struct
import logging


def modbus_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for i in range(8):
            if ((crc & 1) != 0):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


class RTUClient:
    def __init__(self, socket, baudrate):
        self.socket = socket
        self._last_frame_end = time.time()
        if baudrate > 19200:
            self._silent_interval = 1.75/1000
        else:
            self._silent_interval = 3.5 * (1 + 8 + 2) / baudrate

    def read_registers(self, base, length, unit=1):
        request = struct.pack('>B', unit) + \
            struct.pack('>B', 0x03) + \
            struct.pack('>H', base) + \
            struct.pack('>H', length)
        request += struct.pack('<H', modbus_crc(request))
        self.send(request)

        expected_response_length = 5 + (2 * length)
        response = self.recv(expected_response_length)

        assert(struct.unpack('<H', response[-2:])[0] == modbus_crc(response[0:-2]))
        assert(struct.unpack('>B', response[0:1])[0] == unit)
        assert(struct.unpack('>B', response[1:2])[0] == 0x03)
        assert(struct.unpack('>B', response[2:3])[0] == (length * 2))

        registers = []
        for i in range(length):
            pos = 3 + (i * 2)
            registers.append(struct.unpack('>H', response[pos:pos+2])[0])
        return registers

    def write_register(self, register, value, unit=1):
        request = struct.pack('>B', unit) + \
            struct.pack('>B', 0x06) + \
            struct.pack('>H', register) + \
            struct.pack('>H', value)
        request += struct.pack('<H', modbus_crc(request))
        self.send(request)
        expected_response_length = 8
        response = self.recv(expected_response_length)
        assert(response == request)

    def write_registers(self, register, values, unit=1):
        request = struct.pack('>B', unit) + \
            struct.pack('>B', 0x10) + \
            struct.pack('>H', register) + \
            struct.pack('>H', len(values)) + \
            struct.pack('>B', len(values) * 2)
        for value in values:
            request += struct.pack('>H', value)
        request += struct.pack('<H', modbus_crc(request))
        self.send(request)
        expected_response_length = 8
        response = self.recv(expected_response_length)
        assert(struct.unpack('<H', response[-2:])[0] == modbus_crc(response[0:-2]))
        assert(struct.unpack('>B', response[0:1])[0] == unit)
        assert(struct.unpack('>B', response[1:2])[0] == 0x10)
        assert(struct.unpack('>H', response[2:4])[0] == register)
        assert(struct.unpack('>H', response[4:6])[0] == len(values))

    def send(self, data):
        ts = time.time()
        if ts < self._last_frame_end + self._silent_interval:
            to_sleep = self._last_frame_end + self._silent_interval - ts
            logging.debug('Sleeping {} for 3.5 char ({}) quiet period'.format(
                to_sleep,
                self._silent_interval,
            ))
            time.sleep(to_sleep)

        result = self.socket.send(data)
        self._last_frame_end = time.time()
        return result

    def recv(self, size):
        result = self.socket.recv(size)
        self._last_frame_end = time.time()
        return result
