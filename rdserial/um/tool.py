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

import argparse
import json
import time
import datetime
import logging
import statistics

import rdserial.um
import rdserial.um.device


def add_subparsers(subparsers):
    def validate_set_record_threshold(string):
        val = float(string)
        if val not in [x / 100 for x in range(31)]:
            raise argparse.ArgumentTypeError('Must be between 0.00 and 0.30, in 0.01 steps')
        return val

    parser_um24c = subparsers.add_parser('um24c', help='RDTech UM24C')
    parser_um25c = subparsers.add_parser('um25c', help='RDTech UM25C')
    parser_um34c = subparsers.add_parser('um34c', help='RDTech UM34C')

    for parser in (parser_um24c, parser_um25c, parser_um34c):
        parser.add_argument(
            '--next-screen', action='store_true',
            help='Go to the next screen on the display',
        )
        parser.add_argument(
            '--rotate-screen', action='store_true',
            help='Rotate the screen 90 degrees clockwise',
        )
        parser.add_argument(
            '--clear-data-group', action='store_true',
            help='Clear the current data group',
        )
        parser.add_argument(
            '--set-record-threshold', type=validate_set_record_threshold, default=None,
            help='Set the recording threshold, 0.00-0.30 inclusive',
        )
        parser.add_argument(
            '--set-screen-brightness', type=int, choices=range(6), default=None,
            help='Set the screen brightness',
        )
        parser.add_argument(
            '--set-screen-timeout', type=int, choices=range(10), default=None,
            help='Set the screen timeout',
        )

    for parser in (parser_um25c, parser_um34c):
        parser.add_argument(
            '--previous-screen', action='store_true',
            help='Go to the previous screen on the display',
        )
        parser.add_argument(
            '--set-data-group', type=int, choices=range(10), default=None,
            help='Set the selected data group',
        )

    for parser in (parser_um24c,):
        parser.add_argument(
            '--next-data-group', action='store_true',
            help='Change to the next data group',
        )


class Tool:
    def __init__(self):
        self.trends = {}

    def trend_s(self, name, value):
        if not self.args.watch:
            return ''

        if name in self.trends:
            trend = statistics.mean(self.trends[name])
            self.trends[name] = self.trends[name][1:] + [value]
            if value > trend:
                return '\u2197'
            elif value < trend:
                return '\u2198'
            else:
                return ' '
        else:
            self.trends[name] = [value for x in range(self.args.trend_points)]
            return ' '

    def print_json(self, response):
        out = {x: getattr(response, x) for x in response.field_properties}
        out['data_groups'] = [{'amp_hours': x.amp_hours, 'watt_hours': x.watt_hours} for x in out['data_groups']]
        out['collection_time'] = (out['collection_time'] - datetime.datetime.fromtimestamp(0)).total_seconds()
        print(json.dumps(out))

    def print_human(self, response):
        logging.debug('DUMP: {}'.format(repr(response.dump())))
        charging_map = {
            rdserial.um.CHARGING_UNKNOWN: 'Unknown / Normal',
            rdserial.um.CHARGING_QC2: 'Quick Charge 2.0',
            rdserial.um.CHARGING_QC3: 'Quick Charge 3.0',
            rdserial.um.CHARGING_APP2_4A: 'Apple 2.4A',
            rdserial.um.CHARGING_APP2_1A: 'Apple 2.1A',
            rdserial.um.CHARGING_APP1_0A: 'Apple 1.0A',
            rdserial.um.CHARGING_APP0_5A: 'Apple 0.5A',
            rdserial.um.CHARGING_DCP1_5A: 'DCP 1.5A',
            rdserial.um.CHARGING_SAMSUNG: 'Samsung',
        }
        if self.args.command == 'um25c':
            usb_format = 'USB: {:5.03f}V{}, {:6.04f}A{}, {:6.03f}W{}, {:6.01f}Ω{}'
        else:
            usb_format = 'USB: {:5.02f}V{}, {:6.03f}A{}, {:6.03f}W{}, {:6.01f}Ω{}'
        print(usb_format.format(
            response.volts,
            self.trend_s('volts', response.volts),
            response.amps,
            self.trend_s('amps', response.amps),
            response.watts,
            self.trend_s('watts', response.watts),
            response.resistance,
            self.trend_s('resistance', response.resistance),
        ))
        print('Data: {:5.02f}V(+){}, {:5.02f}V(-){}, charging mode: {}'.format(
            response.data_line_positive_volts,
            self.trend_s('data_line_positive_volts', response.data_line_positive_volts),
            response.data_line_negative_volts,
            self.trend_s('data_line_negative_volts', response.data_line_negative_volts),
            charging_map[response.charging_mode],
        ))
        print('Recording {:5}: {:8.03f}Ah{}, {:8.03f}Wh{}, {:6d}{} sec at >= {:4.02f}A'.format(
            '(on)' if response.recording else '(off)',
            response.record_amphours,
            self.trend_s('record_amphours', response.record_amphours),
            response.record_watthours,
            self.trend_s('record_watthours', response.record_watthours),
            response.record_seconds,
            self.trend_s('record_seconds', response.record_seconds),
            response.record_threshold,
        ))

        def make_dgpart(response, idx):
            data_group = response.data_groups[idx]
            return '{}{:d}: {:8.03f}Ah{}, {:8.03f}Wh{}'.format(
                '*' if data_group.group == response.data_group_selected else ' ',
                data_group.group,
                data_group.amp_hours,
                self.trend_s('dg_{}_amp_hours'.format(data_group.group), data_group.amp_hours),
                data_group.watt_hours,
                self.trend_s('dg_{}_watt_hours'.format(data_group.group), data_group.watt_hours),
            )
        print('Data groups:')
        print('    {:32}{}'.format(
          make_dgpart(response, 0),
          make_dgpart(response, 5),
        ))
        print('    {:32}{}'.format(
          make_dgpart(response, 1),
          make_dgpart(response, 6),
        ))
        print('    {:32}{}'.format(
          make_dgpart(response, 2),
          make_dgpart(response, 7),
        ))
        print('    {:32}{}'.format(
          make_dgpart(response, 3),
          make_dgpart(response, 8),
        ))
        print('    {:32}{}'.format(
          make_dgpart(response, 4),
          make_dgpart(response, 9),
        ))

        print('{:>5s}, temperature: {:3d}C{} ({:3d}F{})'.format(
            self.args.command.upper(),
            response.temp_c,
            self.trend_s('temp_c', response.temp_c),
            response.temp_f,
            self.trend_s('temp_f', response.temp_f),
        ))
        print('Screen: {:d}/6, brightness: {:d}/5, timeout: {}'.format(
            response.screen_selected,
            response.screen_brightness,
            '{:d} min'.format(response.screen_timeout) if response.screen_timeout else 'off',
        ))
        if response.collection_time:
            print('Collection time: {}'.format(response.collection_time))

    def send_commands(self):
        for arg, command_val in [
            ('next_screen', b'\xf1'),
            ('rotate_screen', b'\xf2'),
            ('next_data_group', b'\xf3'),
            ('previous_screen', b'\xf3'),
            ('clear_data_group', b'\xf4'),
            ('set_data_group', lambda x: bytes([0xa0 + x])),
            ('set_record_threshold', lambda x: bytes([0xb0 + int(x * 100)])),
            ('set_screen_brightness', lambda x: bytes([0xd0 + x])),
            ('set_screen_timeout', lambda x: bytes([0xe0 + x])),
        ]:
            if not hasattr(self.args, arg):
                continue
            arg_val = getattr(self.args, arg)
            if (arg_val is None) or (arg_val is False):
                continue
            if type(command_val) != bytes:
                command_val = command_val(getattr(self.args, arg))
            logging.info('Setting {} to {}'.format(arg, getattr(self.args, arg)))
            self.dev.send(command_val)
            # Sometimes you can send multiple commands quickly, but sometimes
            # it'll eat commands.  Sleeping 0.5s between commands is safe.
            time.sleep(0.5)

    def loop(self):
        while True:
            try:
                self.dev.send(b'\xf0')
                if self.args.json:
                    self.print_json(rdserial.um.Response(
                        self.dev.recv(),
                        collection_time=datetime.datetime.now(),
                        device_type=self.args.command.upper(),
                    ))
                else:
                    self.print_human(rdserial.um.Response(
                        self.dev.recv(),
                        collection_time=datetime.datetime.now(),
                        device_type=self.args.command.upper(),
                    ))
            except KeyboardInterrupt:
                raise
            except Exception:
                if self.args.watch:
                    logging.exception('An exception has occurred')
                else:
                    raise
            if self.args.watch:
                if not self.args.json:
                    print()
                time.sleep(self.args.watch_seconds)
            else:
                return

    def main(self):
        if self.args.serial_device:
            logging.info('Connecting to {} {}'.format(self.args.command.upper(), self.args.serial_device))
            self.dev = rdserial.um.device.Serial(self.args.serial_device, baudrate=self.args.baud)
        else:
            logging.info('Connecting to {} {}'.format(self.args.command.upper(), self.args.bluetooth_address))
            self.dev = rdserial.um.device.Bluetooth(self.args.bluetooth_address, port=self.args.bluetooth_port)
        self.dev.connect()
        logging.info('Connection established')
        logging.info('')
        time.sleep(self.args.connect_delay)
        try:
            self.send_commands()
            self.loop()
        except KeyboardInterrupt:
            pass
        self.dev.close()


def main(parent):
    r = Tool()
    r.args = parent.args
    return r.main()
