# rdserialtool
# Copyright (C) 2019-2021 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0

import argparse
import sys
import os
import logging
import time

from rdserial import __version__
import rdserial.device
import rdserial.um.tool
import rdserial.dps.tool


def parse_args(argv=None):
    """Parse user arguments."""
    if argv is None:
        argv = sys.argv

    def loose_bool(val):
        return val.lower() in ('on', 'true', 'yes')

    def validate_set_record_threshold(string):
        val = float(string)
        if val not in [x / 100 for x in range(31)]:
            raise argparse.ArgumentTypeError('Must be between 0.00 and 0.30, in 0.01 steps')
        return val

    parser = argparse.ArgumentParser(
        description='rdserialtool ({})'.format(__version__),
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

    supported_devices = []
    supported_devices += rdserial.um.tool.supported_devices
    supported_devices += rdserial.dps.tool.supported_devices
    parser.add_argument(
        '--device', '-d', required=True,
        choices=sorted(supported_devices),
        help='Device type',
    )

    device_group = parser.add_mutually_exclusive_group(required=True)
    device_group.add_argument(
        '--bluetooth-address', '-b',
        help='Bluetooth EUI-48 address of the device',
    )
    device_group.add_argument(
        '--serial-device', '-s',
        help='Serial filename (e.g. /dev/rfcomm0) of the device',
    )

    parser.add_argument(
        '--bluetooth-port', type=int, default=1,
        help='Bluetooth RFCOMM port number',
    )
    parser.add_argument(
        '--baud', type=int, default=9600,
        help='Serial port baud rate',
    )
    parser.add_argument(
        '--connect-delay', type=float, default=0.3,
        help='Seconds to wait after connecting to the serial port',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output JSON data',
    )
    parser.add_argument(
        '--watch', action='store_true',
        help='Repeat data collection until cancelled',
    )
    parser.add_argument(
        '--watch-seconds', type=float, default=2.0,
        help='Number of seconds between collections in watch mode',
    )
    parser.add_argument(
        '--trend-points', type=int, default=5,
        help='Number of points to remember for determining a trend in watch mode',
    )

    parser_group_dps = parser.add_argument_group(
        'DPS/RD-related arguments'
    )

    parser_group_dps.add_argument(
        '--modbus-unit', type=int, default=1,
        help='Modbus unit number',
    )
    parser_group_dps.add_argument(
        '--group', type=int, action='append',
        help='Display/set selected group(s)',
    )
    parser_group_dps.add_argument(
        '--all-groups', action='store_true',
        help='Display/set all groups',
    )

    parser_group_dps.add_argument(
        '--set-volts', type=float, default=None,
        help='Set voltage setting',
    )
    parser_group_dps.add_argument(
        '--set-amps', type=float, default=None,
        help='Set current setting',
    )
    parser_group_dps.add_argument(
        '--set-clock', action='store_true',
        help='Set clock to current time [RD]',
    )

    onoff_group = parser_group_dps.add_mutually_exclusive_group(required=False)
    onoff_group.add_argument(
        '--set-output-state', type=loose_bool, dest='set_output_state', default=None,
        help='Set output on/off',
    )
    onoff_group.add_argument(
        '--on', action='store_true', dest='set_output_state',
        help='Set output on',
    )
    onoff_group.add_argument(
        '--off', action='store_false', dest='set_output_state',
        help='Set output off',
    )

    parser_group_dps.add_argument(
        '--set-key-lock', type=loose_bool, default=None,
        help='Set key lock on/off',
    )
    parser_group_dps.add_argument(
        '--set-brightness', type=int, choices=range(6), default=None,
        help='Set screen brightness',
    )
    parser_group_dps.add_argument(
        '--load-group', type=int, choices=range(10), default=None,
        help='Load group settings into group 0',
    )

    parser_group_dps.add_argument(
        '--set-group-volts', type=float, default=None,
        help='Set group voltage setting',
    )
    parser_group_dps.add_argument(
        '--set-group-amps', type=float, default=None,
        help='Set group current setting',
    )
    parser_group_dps.add_argument(
        '--set-group-cutoff-volts', type=float, default=None,
        help='Set group cutoff volts',
    )
    parser_group_dps.add_argument(
        '--set-group-cutoff-amps', type=float, default=None,
        help='Set group cutoff amps',
    )
    parser_group_dps.add_argument(
        '--set-group-cutoff-watts', type=float, default=None,
        help='Set group cutoff watts',
    )
    parser_group_dps.add_argument(
        '--set-group-brightness', type=int, choices=range(6), default=None,
        help='Set group screen brightness',
    )
    parser_group_dps.add_argument(
        '--set-group-maintain-output', type=loose_bool, default=None,
        help='Set group maintain output state during group change',
    )
    parser_group_dps.add_argument(
        '--set-group-poweron-output', type=loose_bool, default=None,
        help='Set group enable output on power-on',
    )

    parser_group_um = parser.add_argument_group(
        'UM-related arguments'
    )

    parser_group_um.add_argument(
        '--next-screen', action='store_true',
        help='Go to the next screen on the display',
    )
    parser_group_um.add_argument(
        '--rotate-screen', action='store_true',
        help='Rotate the screen 90 degrees clockwise',
    )
    parser_group_um.add_argument(
        '--clear-data-group', action='store_true',
        help='Clear the current data group',
    )
    parser_group_um.add_argument(
        '--set-record-threshold', type=validate_set_record_threshold, default=None,
        help='Set the recording threshold, 0.00-0.30 inclusive',
    )
    parser_group_um.add_argument(
        '--set-screen-brightness', type=int, choices=range(6), default=None,
        help='Set the screen brightness',
    )
    parser_group_um.add_argument(
        '--set-screen-timeout', type=int, choices=range(10), default=None,
        help='Set the screen timeout',
    )

    parser_group_um.add_argument(
        '--previous-screen', action='store_true',
        help='Go to the previous screen on the display',
    )
    parser_group_um.add_argument(
        '--set-data-group', type=int, choices=range(10), default=None,
        help='Set the selected data group',
    )

    parser_group_um.add_argument(
        '--next-data-group', action='store_true',
        help='Change to the next data group',
    )

    parser.add_argument(
        '--verbose', action='store_true', default=None,
        help='Remove some display',
    )

    args = parser.parse_args(args=argv[1:])

    return args


class RDSerialTool:
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

    def main(self):
        self.args = parse_args()
        self.setup_logging()
        if self.args.verbose is None:
            logging.info('rdumtool {}'.format(__version__))
            logging.info('Copyright (C) 2019 Ryan Finnie')
            logging.info('')
            if self.args.serial_device:
                logging.info('Connecting to {} {}'.format(self.args.device.upper(), self.args.serial_device))
                self.socket = rdserial.device.Serial(
                    self.args.serial_device,
                    baudrate=self.args.baud,
                )
            else:
                logging.info('Connecting to {} {}'.format(self.args.device.upper(), self.args.bluetooth_address))
                self.socket = rdserial.device.Bluetooth(
                    self.args.bluetooth_address,
                    port=self.args.bluetooth_port,
                )
            self.socket.connect()
            logging.info('Connection established')
            logging.info('')
        else:
            if self.args.serial_device:
                self.socket = rdserial.device.Serial(
                    self.args.serial_device,
                    baudrate=self.args.baud,
                )
            else:
                self.socket = rdserial.device.Bluetooth(
                    self.args.bluetooth_address,
                    port=self.args.bluetooth_port,
                )
            self.socket.connect()
        
        time.sleep(self.args.connect_delay)

        if self.args.device in rdserial.um.tool.supported_devices:
            tool = rdserial.um.tool.Tool(self)
        elif self.args.device in rdserial.dps.tool.supported_devices:
            tool = rdserial.dps.tool.Tool(self)
        ret = tool.main()

        self.socket.close()
        return ret


def main():
    return RDSerialTool().main()


if __name__ == '__main__':
    sys.exit(main())
