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

import datetime
import logging

PROTECTION_GOOD = 0
PROTECTION_OV = 1
PROTECTION_OC = 2
PROTECTION_OP = 3


class DeviceState:
    def __init__(self, collection_time=None):
        self.register_properties = {
            'model': {
                'description': 'Device model',
                'register': 0x00,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'serial': {
                'description': 'Device serial',
                'register': 0x02,  # 0x01 high?
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'firmware': {
                'description': 'Device firmware',
                'register': 0x03,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'fan_temp_c': {
                'description': 'Fan start temperature (C)',
                'register': 0x05,  # 0x04 high?
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'fan_temp_f': {
                'description': 'Fan start temperature (F)',
                'register': 0x07,  # 0x06 high?
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x08,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x09,
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
            'volts': {
                'description': 'Output volts',
                'register': 0x0a,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'amps': {
                'description': 'Output amps',
                'register': 0x0b,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'watts': {
                'description': 'Output watts',
                'register': 0x0d,  # 0x0c high?
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'input_volts': {
                'description': 'Input volts',
                'register': 0x0e,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'key_lock': {
                'description': 'Key lock',
                'register': 0x0f,
                'from_int': lambda x: bool(x),
                'to_int': lambda x: int(x),
            },
            'protection': {
                'description': 'Protection status',
                'register': 0x10,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'constant_current': {
                'description': 'Constant current mode',
                'register': 0x11,
                'from_int': lambda x: bool(x),
                'to_int': lambda x: int(x),
            },
            'output_state': {
                'description': 'Output state',
                'register': 0x12,
                'from_int': lambda x: bool(x),
                'to_int': lambda x: int(x),
            },
            'group_loader': {
                'description': 'Group loader',
                'register': 0x13,
                'from_int': lambda x: 0,
                'to_int': lambda x: int(x),
            },
            # 0x14 - 0x2f: All 0
            # 0x21: Unknown, 1/2/3 observed
            'temp_c': {
                'description': 'Temperature (C)',
                'register': 0x23,  # 0x22 high?
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'temp_f': {
                'description': 'Temperature (F)',
                'register': 0x25,  # 0x24 high?
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            # 0x26 / 0x27 mAh
            # 0x28 / 0x29 mWh
            # 0x30 - 0x35 date / time
            'brightness': {
                'description': 'Brightness level',
                'register': 0x48,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'ovp': {
                'description': 'Over-voltage limit (V)',
                'register': 0x52,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'ocp': {
                'description': 'Over-current limit (A)',
                'register': 0x53,
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
        }

        if collection_time is None:
            collection_time = datetime.datetime.now()
        self.collection_time = collection_time
        for name in self.register_properties:
            setattr(self, name, self.register_properties[name]['from_int'](0))
        self.groups = {}

    def load(self, data, offset=0):
        pos_map = {v['register']: k for k, v in self.register_properties.items()}
        i = 0
        for raw_val in data:
            val_pos = offset + i
            logging.debug('Register 0x{:02x}: {}'.format(val_pos, raw_val))
            if val_pos in pos_map:
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1


class GroupState:
    def __init__(self, group):
        self.group = group
        self.register_properties = {
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x50 + (0x04 * group),
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x51 + (0x04 * group),
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
            'cutoff_volts': {
                'description': 'Volts cutoff',
                'register': 0x52 + (0x04 * group),
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'cutoff_amps': {
                'description': 'Amps cutoff',
                'register': 0x53 + (0x04 * group),
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
        }

        for name in self.register_properties:
            setattr(self, name, self.register_properties[name]['from_int'](0))

    def load(self, data, offset=0):
        pos_map = {v['register']: k for k, v in self.register_properties.items()}
        i = 0
        logging.debug(pos_map)
        for raw_val in data:
            val_pos = offset + i
            logging.debug((val_pos, raw_val))
            if val_pos in pos_map:
                logging.debug('yes')
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1
