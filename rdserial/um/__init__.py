# rdserialtool
# Copyright (C) 2019-2021 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

import struct
import datetime
import logging

CHARGING_UNKNOWN = 0
CHARGING_QC2 = 1
CHARGING_QC3 = 2
CHARGING_APP2_4A = 3
CHARGING_APP2_1A = 4
CHARGING_APP1_0A = 5
CHARGING_APP0_5A = 6
CHARGING_DCP1_5A = 7
CHARGING_SAMSUNG = 8


class DataGroup:
    group = 0
    amp_hours = 0
    watt_hours = 0

    def __repr__(self):
        return ('<DataGroup {}: {:0.03f}Ah, {:0.03f}Wh>'.format(
            self.group,
            self.amp_hours,
            self.watt_hours,
        ))

    def __init__(self, group=0):
        self.group = group


class Response:
    def __repr__(self):
        return ('<Response: {} at {}, {:0.02f}V, {:0.03f}A>'.format(
            self.device_type,
            self.collection_time,
            self.volts,
            self.amps,
        ))

    def __init__(self, data=None, collection_time=None, device_type='UM24C'):
        self.device_type = device_type
        if device_type == 'UM25C':
            self.device_multiplier = 10
        else:
            self.device_multiplier = 1

        self.field_properties = {
            'start': {
                'description': 'Start bytes',
                'position': 0,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'volts': {
                'description': 'Volts',
                'position': 2,
                'length': 2,
                'from_int': lambda x: x / (100 * self.device_multiplier),
                'to_int': lambda x: int(x * (100 * self.device_multiplier)),
            },
            'amps': {
                'description': 'Amps',
                'position': 4,
                'length': 2,
                'from_int': lambda x: x / (1000 * self.device_multiplier),
                'to_int': lambda x: int(x * (1000 * self.device_multiplier)),
            },
            'watts': {
                'description': 'Watts',
                'position': 6,
                'length': 4,
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
            'temp_c': {
                'description': 'Temperature (Celsius)',
                'position': 10,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'temp_f': {
                'description': 'Temperature (Fahrenheit)',
                'position': 12,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'data_group_selected': {
                'description': 'Currently selected data group',
                'position': 14,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'data_line_positive_volts': {
                'description': 'Positive data line volts',
                'position': 96,
                'length': 2,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'data_line_negative_volts': {
                'description': 'Negative data line volts',
                'position': 98,
                'length': 2,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'charging_mode': {
                'description': 'Charging mode',
                'position': 100,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'record_amphours': {
                'description': 'Recorded amp-hours',
                'position': 102,
                'length': 4,
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
            'record_watthours': {
                'description': 'Recorded watt-hours',
                'position': 106,
                'length': 4,
                'from_int': lambda x: x / 1000,
                'to_int': lambda x: int(x * 1000),
            },
            'record_threshold': {
                'description': 'Recording threshold (Amps)',
                'position': 110,
                'length': 2,
                'from_int': lambda x: x / 100,
                'to_int': lambda x: int(x * 100),
            },
            'record_seconds': {
                'description': 'Recorded time (Seconds)',
                'position': 112,
                'length': 4,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'recording': {
                'description': 'Recording',
                'position': 116,
                'length': 2,
                'from_int': lambda x: bool(x),
                'to_int': lambda x: int(x),
            },
            'screen_timeout': {
                'description': 'Screen timeout (Minutes)',
                'position': 118,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'screen_brightness': {
                'description': 'Screen brightness',
                'position': 120,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'resistance': {
                'description': 'Resistance (Ohms)',
                'position': 122,
                'length': 4,
                'from_int': lambda x: x / 10,
                'to_int': lambda x: int(x * 10),
            },
            'screen_selected': {
                'description': 'Currently selected screen',
                'position': 126,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
            'end': {
                'description': 'End bytes',
                'position': 128,
                'length': 2,
                'from_int': lambda x: x,
                'to_int': lambda x: int(x),
            },
        }

        if collection_time is None:
            collection_time = datetime.datetime.now()
        self.collection_time = collection_time
        for name in self.field_properties:
            setattr(self, name, 0)
        self.data_groups = [DataGroup(x) for x in range(10)]

        if data:
            self.load(data)

    def dump(self):
        data = bytearray(130)
        for name in self.field_properties:
            pos = self.field_properties[name]['position']
            pos_len = self.field_properties[name]['length']
            if pos_len == 2:
                pack_format = '>H'
            elif pos_len == 4:
                pack_format = '>L'
            else:
                pack_format = 'B'
            conversion_dump = self.field_properties[name]['to_int']
            data[pos:pos+pos_len] = struct.pack(pack_format, conversion_dump(getattr(self, name)))

        for data_group in self.data_groups:
            if (data_group.group > 9) or (data_group.group < 0):
                continue
            pos = 16 + (data_group.group * 8)
            data[pos:pos+4] = struct.pack('>L', int(data_group.amp_hours * 1000))
            data[pos+4:pos+8] = struct.pack('>L', int(data_group.watt_hours * 1000))
        return bytes(data)

    def load(self, data):
        if len(data) != 130:
            raise ValueError('Invalid data length', data)
        logging.debug('Start: 0x{:02x}{:02x}, end: 0x{:02x}{:02x}'.format(data[0], data[1], data[128], data[129]))
        for name in self.field_properties:
            pos = self.field_properties[name]['position']
            pos_len = self.field_properties[name]['length']
            if pos_len == 2:
                pack_format = '>H'
            elif pos_len == 4:
                pack_format = '>L'
            else:
                pack_format = 'B'
            conversion_load = self.field_properties[name]['from_int']
            val = conversion_load(struct.unpack(pack_format, data[pos:pos+pos_len])[0])
            setattr(self, name, val)

        self.data_groups = []
        for i in range(10):
            data_group = DataGroup(i)
            pos = 16 + (i * 8)
            data_group.amp_hours = struct.unpack('>L', data[pos:pos+4])[0] / 1000
            data_group.watt_hours = struct.unpack('>L', data[pos+4:pos+8])[0] / 1000
            self.data_groups.append(data_group)
