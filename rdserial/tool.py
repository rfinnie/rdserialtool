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
import sys
import os
import logging

from rdserial import __version__
import rdserial.um.tool
try:
    import rdserial.dps.tool
    HAS_DPS = True
except ImportError:
    HAS_DPS = False


def parse_args(argv=None):
    """Parse user arguments."""
    if argv is None:
        argv = sys.argv

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

    device_group = parser.add_mutually_exclusive_group(required=True)
    device_group.add_argument(
        '--bluetooth-address', '-d',
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
        '--watch', type=float, const=2.0, nargs='?', default=None,
        help='Repeat every WATCH seconds, default 2 if flag but no value',
    )
    parser.add_argument(
        '--trend-points', type=int, default=5,
        help='Number of points to remember for determining a trend in watch mode',
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')
    rdserial.um.tool.add_subparsers(subparsers)
    if HAS_DPS:
        rdserial.dps.tool.add_subparsers(subparsers)

    args = parser.parse_args(args=argv[1:])
    return args


class RDTechTool:
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

        logging.info('rdserialtool {}'.format(__version__))
        logging.info('Copyright (C) 2019 Ryan Finnie')
        logging.info('')

        if self.args.command in ('um24c', 'um25c', 'um34c'):
            return rdserial.um.tool.main(self)
        elif self.args.command == 'dps':
            return rdserial.dps.tool.main(self)


def main():
    return RDTechTool().main()


if __name__ == '__main__':
    sys.exit(main())
