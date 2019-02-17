# rdumtool
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
import sys
import os
import json
import time
import datetime
import logging
import statistics

from . import __version__
import rdum


def parse_args(argv=None):
    """Parse user arguments."""
    if argv is None:
        argv = sys.argv

    def validate_set_record_threshold(string):
        val = float(string)
        if val not in [x / 100 for x in range(31)]:
            raise argparse.ArgumentTypeError('Must be between 0.00 and 0.30, in 0.01 steps')
        return val

    parser = argparse.ArgumentParser(
        description='rdumtool ({})'.format(__version__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog=os.path.basename(argv[0]),
    )

    parser.add_argument(
        '--version', '-V', action='version',
        version=__version__,
        help='Report the program version',
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress human-readable stderr information',
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Print extra debugging information.',
    )
    parser.add_argument(
        '--device-type', '-t', choices=['UM24C', 'UM25C', 'UM34C'], default=None,
        help='Device type',
    )
    device_group = parser.add_mutually_exclusive_group(required=False)
    device_group.add_argument(
        '--bluetooth-address', '-d',
        help='Bluetooth EUI-48 address of the device',
    )
    device_group.add_argument(
        '--serial-device', '-s',
        help='Serial filename (e.g. /dev/rfcomm0) of the device',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output JSON data',
    )
    parser.add_argument(
        '--watch', type=float, const=2.0, nargs='?', default=None,
        help='Repeat every WATCH seconds, default 2 if flag but no value',
    )
    parser.add_argument(
        '--trend-points', type=int, default=5,
        help='Number of points to remember for determining a trend in watch mode',
    )
    parser.add_argument(
        '--next-screen', action='store_true',
        help='Go to the next screen on the display',
    )
    parser.add_argument(
        '--previous-screen', action='store_true',
        help='[UM25C, UM34C] Go to the previous screen on the display',
    )
    parser.add_argument(
        '--rotate-screen', action='store_true',
        help='Rotate the screen 90 degrees clockwise',
    )
    parser.add_argument(
        '--set-data-group', type=int, choices=range(10), default=None,
        help='[UM25C, UM34C] Set the selected data group',
    )
    parser.add_argument(
        '--next-data-group', action='store_true',
        help='[UM24C] Change to the next data group',
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

    args = parser.parse_args(args=argv[1:])

    for arg, compat in [
        ('next_data_group', ['UM24C']),
        ('previous_screen', ['UM25C', 'UM34C']),
        ('set_data_group', ['UM25C', 'UM34C']),
    ]:
        arg_val = getattr(args, arg)
        if (arg_val is None) or (arg_val is False):
            continue
        if args.device_type not in compat:
            parser.error('--{} not supported on device {}'.format(
                arg.replace('_', '-'), args.device_type
            ))

    return args


class RDUMTool:
    def __init__(self):
        self.trends = {}

    def trend_s(self, name, value):
        if not self.args.watch:
            return ''

        if name in self.trends:
            trend = statistics.mean(self.trends[name])
            self.trends[name] = self.trends[name][1:] + [value]
            if value > trend:
                return '↗'
            elif value < trend:
                return '↘'
            else:
                return ' '
        else:
            self.trends[name] = [value for x in range(self.args.trend_points)]
            return ' '

    def print_json(self, response):
        out = {x: getattr(response, x) for x in response.labels}
        out['data_groups'] = [{'amp_hours': x.amp_hours, 'watt_hours': x.watt_hours} for x in out['data_groups']]
        out['collection_time'] = (out['collection_time'] - datetime.datetime.fromtimestamp(0)).total_seconds()
        print(json.dumps(out))

    def print_human(self, response):
        logging.debug('DUMP: {}'.format(repr(response.dump())))
        charging_map = {
            rdum.CHARGING_UNKNOWN: 'Unknown / Normal',
            rdum.CHARGING_QC2: 'Quick Charge 2.0',
            rdum.CHARGING_QC3: 'Quick Charge 3.0',
            rdum.CHARGING_APP2_4A: 'Apple 2.4A',
            rdum.CHARGING_APP2_1A: 'Apple 2.1A',
            rdum.CHARGING_APP1_0A: 'Apple 1.0A',
            rdum.CHARGING_APP0_5A: 'Apple 0.5A',
            rdum.CHARGING_DCP1_5A: 'DCP 1.5A',
            rdum.CHARGING_SAMSUNG: 'Samsung',
        }
        if self.args.device_type == 'UM25C':
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
            self.args.device_type,
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

    def setup_logging(self):
        logging_format = '%(message)s'
        if self.args.debug:
            logging_level = logging.DEBUG
            logging_format = '%(asctime)s %(levelname)s: %(message)s'
        elif self.args.quiet:
            logging_level = logging.ERROR
        else:
            logging_level = logging.INFO
        logging.basicConfig(
            format=logging_format,
            level=logging_level,
        )

    def setup_device(self):
        if self.args.serial_device:
            if self.args.device_type is None:
                logging.error('Device type must be specified for this device')
                return False
            logging.info('Connecting to {} {}'.format(self.args.device_type, self.args.serial_device))
            self.dev = rdum.DeviceSerial(self.args.serial_device)
            logging.info('Connection established')
            logging.info('')
            return

        self.dev = rdum.DeviceBluetooth()
        if not self.args.bluetooth_address:
            logging.info('Searching for Bluetooth devices, please wait')
            for address, name, bt_class in self.dev.scan():
                logging.info('    {} - {}'.format(address, name))
                if name in ('UM24C', 'UM25C', 'UM34C'):
                    self.args.bluetooth_address = address
                    self.args.device_type = name
            if not self.args.bluetooth_address:
                logging.error('No suitable Bluetooth device found')
                return False
        if self.args.device_type is None:
            logging.warn('Device type not specified, trying to figure out (not reliable; please specify)')
            name = self.dev.lookup_name(self.args.bluetooth_address)
            if name in ('UM24C', 'UM25C', 'UM34C'):
                logging
                self.args.device_type = name
            else:
                logging.error('Device type must be specified for this device')
                return False
        logging.info('Connecting to {} {}'.format(self.args.device_type, self.args.bluetooth_address))
        self.dev.connect(self.args.bluetooth_address)
        logging.info('Connection established')
        logging.info('')

    def loop(self):
        while True:
            try:
                self.dev.send(b'\xf0')
                if self.args.json:
                    self.print_json(rdum.Response(
                        self.dev.recv(),
                        collection_time=datetime.datetime.now(),
                        device_type=self.args.device_type,
                    ))
                else:
                    self.print_human(rdum.Response(
                        self.dev.recv(),
                        collection_time=datetime.datetime.now(),
                        device_type=self.args.device_type,
                    ))
            except KeyboardInterrupt:
                raise
            except Exception:
                if self.args.watch is None:
                    raise
                else:
                    logging.exception('An exception has occurred')
            if self.args.watch is not None:
                if not self.args.json:
                    print()
                if self.args.watch > 0:
                    time.sleep(self.args.watch)
            else:
                return

    def main(self):
        self.args = parse_args()
        self.setup_logging()

        logging.info('rdumtool {}'.format(__version__))
        logging.info('Copyright (C) 2019 Ryan Finnie')
        logging.info('')

        if self.setup_device() is False:
            return 1
        try:
            self.send_commands()
            self.loop()
        except KeyboardInterrupt:
            pass
        self.dev.close()


def main():
    return(RDUMTool().main())


if __name__ == '__main__':
    sys.exit(main())
