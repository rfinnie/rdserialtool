# rdserialtool
# Copyright (C) 2019-2021 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

import datetime

PROTECTION_GOOD = 0
PROTECTION_OV = 1
PROTECTION_OC = 2
PROTECTION_OP = 3


def _simple_int(multiple=1):
    return {
        'from_int': lambda x: x / multiple,
        'to_int': lambda x: int(x * multiple),
    }


def _simple_bool():
    return {
        'from_int': lambda x: bool(x),
        'to_int': lambda x: int(x),
    }


class DPSDeviceState:
    def __init__(self, collection_time=None):
        self.register_properties = {
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x00,
                **_simple_int(100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x01,
                **_simple_int(100),
            },
            'volts': {
                'description': 'Output volts',
                'register': 0x02,
                **_simple_int(100),
            },
            'amps': {
                'description': 'Output amps',
                'register': 0x03,
                **_simple_int(100),
            },
            'watts': {
                'description': 'Output watts',
                'register': 0x04,
                **_simple_int(100),
            },
            'input_volts': {
                'description': 'Input volts',
                'register': 0x05,
                **_simple_int(100),
            },
            'key_lock': {
                'description': 'Key lock',
                'register': 0x06,
                **_simple_bool(),
            },
            'protection': {
                'description': 'Protection status',
                'register': 0x07,
                **_simple_int(),
            },
            'constant_current': {
                'description': 'Constant current mode',
                'register': 0x08,
                **_simple_bool(),
            },
            'output_state': {
                'description': 'Output state',
                'register': 0x09,
                **_simple_bool(),
            },
            'brightness': {
                'description': 'Brightness level',
                'register': 0x0a,
                **_simple_int(),
            },
            'model': {
                'description': 'Device model',
                'register': 0x0b,
                **_simple_int(),
            },
            'firmware': {
                'description': 'Device firmware',
                'register': 0x0c,
                **_simple_int(),
            },
            'group_loader': {
                'description': 'Group loader',
                'register': 0x23,
                'from_int': lambda x: 0,  # Write-only
                'to_int': lambda x: int(x),
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
            if val_pos in pos_map:
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1


class DPSGroupState:
    def __init__(self, group):
        self.group = group
        self.register_properties = {
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x50 + (0x10 * group),
                **_simple_int(100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x51 + (0x10 * group),
                **_simple_int(1000),
            },
            'cutoff_volts': {
                'description': 'Volts cutoff',
                'register': 0x52 + (0x10 * group),
                **_simple_int(100),
            },
            'cutoff_amps': {
                'description': 'Amps cutoff',
                'register': 0x53 + (0x10 * group),
                **_simple_int(1000),
            },
            'cutoff_watts': {
                'description': 'Watts cutoff',
                'register': 0x54 + (0x10 * group),
                **_simple_int(10),
            },
            'brightness': {
                'description': 'Brightness level',
                'register': 0x55 + (0x10 * group),
                **_simple_int(),
            },
            'maintain_output': {
                'description': 'Maintain output state during group change',
                'register': 0x56 + (0x10 * group),
                **_simple_bool(),
            },
            'poweron_output': {
                'description': 'Enable output on power-on',
                'register': 0x57 + (0x10 * group),
                **_simple_bool(),
            },
        }

        for name in self.register_properties:
            setattr(self, name, self.register_properties[name]['from_int'](0))

    def load(self, data, offset=0):
        pos_map = {v['register']: k for k, v in self.register_properties.items()}
        i = 0
        for raw_val in data:
            val_pos = offset + i
            if val_pos in pos_map:
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1


class RDDeviceState:
    def __init__(self, collection_time=None):
        self.register_properties = {
            'model': {
                'description': 'Device model',
                'register': 0x00,
                **_simple_int(),
            },
            'serial': {
                'description': 'Device serial',
                'register': 0x02,  # 0x01 high?
                **_simple_int(),
            },
            'firmware': {
                'description': 'Device firmware',
                'register': 0x03,
                **_simple_int(),
            },
            'fan_temp_c': {
                'description': 'Fan start temperature (C)',
                'register': 0x05,  # 0x04 high?
                **_simple_int(),
            },
            'fan_temp_f': {
                'description': 'Fan start temperature (F)',
                'register': 0x07,  # 0x06 high?
                **_simple_int(),
            },
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x08,
                **_simple_int(100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x09,
                **_simple_int(1000),
            },
            'volts': {
                'description': 'Output volts',
                'register': 0x0a,
                **_simple_int(100),
            },
            'amps': {
                'description': 'Output amps',
                'register': 0x0b,
                **_simple_int(100),
            },
            'watts': {
                'description': 'Output watts',
                'register': 0x0d,  # 0x0c high?
                **_simple_int(100),
            },
            'input_volts': {
                'description': 'Input volts',
                'register': 0x0e,
                **_simple_int(100),
            },
            'key_lock': {
                'description': 'Key lock',
                'register': 0x0f,
                **_simple_bool(),
            },
            'protection': {
                'description': 'Protection status',
                'register': 0x10,
                **_simple_int(),
            },
            'constant_current': {
                'description': 'Constant current mode',
                'register': 0x11,
                **_simple_bool(),
            },
            'output_state': {
                'description': 'Output state',
                'register': 0x12,
                **_simple_bool(),
            },
            'group_loader': {
                'description': 'Group loader',
                'register': 0x13,
                'from_int': lambda x: 0,  # Write-only
                'to_int': lambda x: int(x),
            },
            # 0x14 - 0x2f: All 0
            # 0x21: Unknown, 1/2/3 observed
            'temp_c': {
                'description': 'Temperature (C)',
                'register': 0x23,  # 0x22 high?
                **_simple_int(),
            },
            'temp_f': {
                'description': 'Temperature (F)',
                'register': 0x25,  # 0x24 high?
                **_simple_int(),
            },
            'cumulative_charge': {
                'description': 'Cumulative charge (Ah)',
                'register': 0x27,  # 0x26 high?
                **_simple_int(1000),
            },
            'cumulative_energy': {
                'description': 'Cumulative energy (Wh)',
                'register': 0x29,  # 0x28 high?
                **_simple_int(1000),
            },
            'datetime_year': {'description': 'Year', 'register': 0x30, **_simple_int()},
            'datetime_month': {'description': 'Month', 'register': 0x31, **_simple_int()},
            'datetime_day': {'description': 'Day', 'register': 0x32, **_simple_int()},
            'datetime_hour': {'description': 'Hour', 'register': 0x33, **_simple_int()},
            'datetime_minute': {'description': 'Minute', 'register': 0x34, **_simple_int()},
            'datetime_second': {'description': 'Second', 'register': 0x35, **_simple_int()},
            'brightness': {
                'description': 'Brightness level',
                'register': 0x48,
                **_simple_int(),
            },
            'ovp': {
                'description': 'Over-voltage limit (V)',
                'register': 0x52,
                **_simple_int(100),
            },
            'ocp': {
                'description': 'Over-current limit (A)',
                'register': 0x53,
                **_simple_int(1000),
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
            if val_pos in pos_map:
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1


class RDGroupState:
    def __init__(self, group):
        self.group = group
        self.register_properties = {
            'setting_volts': {
                'description': 'Voltage setting',
                'register': 0x50 + (0x04 * group),
                **_simple_int(100),
            },
            'setting_amps': {
                'description': 'Amperage setting',
                'register': 0x51 + (0x04 * group),
                **_simple_int(1000),
            },
            'cutoff_volts': {
                'description': 'Volts cutoff',
                'register': 0x52 + (0x04 * group),
                **_simple_int(100),
            },
            'cutoff_amps': {
                'description': 'Amps cutoff',
                'register': 0x53 + (0x04 * group),
                **_simple_int(1000),
            },
        }

        for name in self.register_properties:
            setattr(self, name, self.register_properties[name]['from_int'](0))

    def load(self, data, offset=0):
        pos_map = {v['register']: k for k, v in self.register_properties.items()}
        i = 0
        for raw_val in data:
            val_pos = offset + i
            if val_pos in pos_map:
                name = pos_map[val_pos]
                translation = self.register_properties[name]['from_int']
                val = translation(raw_val)
                setattr(self, name, val)
            i = i + 1
