# rdumtool - RDTech UM24C Bluetooth interface tool

*This script is currently in an early stage and could change significantly.*

The [RDTech UM24C](https://www.aliexpress.com/item/RD-UM24-UM24C-for-APP-USB-2-0-LCD-Display-Voltmeter-ammeter-battery-charge-voltage-current/32845522857.html) is a low-cost USB pass-through power measurement tool, and supports a decent number of collection features, as well as full control via Bluetooth.  (The UM24 supports the same features as the UM24C, but without Bluetooth control.)  This program implements all exposed commands and data collection exposed by the UM24C's Bluetooth interface.

## Setup

```
$ bluetoothctl

[bluetooth]# scan on
Discovery started
[bluetooth]# list
00:90:72:56:98:D7 UM24C
# MAC will vary by device
[bluetooth]# pair 00:90:72:56:98:D7
Attempting to pair with 00:90:72:56:98:D7
[CHG] Device 00:90:72:56:98:D7 Connected: yes
Request PIN code
[UM24C[agent] Enter PIN code: 1234
# Enter literal "1234" here
[bluetooth]# trust 00:90:72:56:98:D7
[CHG] Device 00:90:72:56:98:D7 Trusted: yes
Changing 00:90:72:56:98:D7 trust succeeded
```

## Usage

At this point, to use the Bluetooth device directly, you will need [PyBluez](https://pypi.org/project/PyBluez/).  Debian and Ubuntu only added Python 3 versions (python3-bluez) recently (as of early 2019), so if not available via apt, you will need to install it via pip.  With PyBluez available, you can run:

```
$ rdumtool --bluetooth-device=00:90:72:56:98:D7
```

Alternatively, with [pyserial](https://pypi.org/project/pyserial/) required, you can bind it to a serial device:

```
$ sudo rfcomm bind 0 00:90:72:56:98:D7
$ rdumtool --serial-device=/dev/rfcomm0
```

Without any additional arguments, rdumtool will display all information available from the UM24C.  There are various additional flags to set parameters in the UM24C such as threshold logging; see ```rdumtool --help``` for details.

## Example

```
$ rdumtool --bluetooth-device=00:90:72:56:98:D7 --rotate-screen --set-record-threshold=0.20

$ rdumtool --bluetooth-device=00:90:72:56:98:D7
rdumtool 1.0
Copyright (C) 2019 Ryan Finnie

USB:  5.08V,  0.166A,  0.843W,   30.6Ω
Data:  2.99V(+),  0.00V(-), charging mode: unknown (normal)
Recording (on) :    0.009Ah,    0.046Wh,  197 sec at >= 0.20A
Data groups:
     0:    0.015Ah,    0.077Wh       5:    0.000Ah,    0.000Wh
     1:    0.000Ah,    0.000Wh       6:    0.000Ah,    0.000Wh
    *2:    0.040Ah,    0.204Wh       7:    0.000Ah,    0.000Wh
     3:    0.000Ah,    0.000Wh       8:    0.000Ah,    0.000Wh
     4:    0.000Ah,    0.000Wh       9:    0.000Ah,    0.000Wh
Temp:  25C ( 77F)
Screen: 1/6, brightness: 5/5, timeout: 2 min
```

## Miscellaneous

Thanks to [the sigrok wiki](https://sigrok.org/wiki/RDTech_UM24C) for a reverse engineering of the UM24C's communication protocol, which was referenced to produce this tool.

I currently have a UM25C and a UM34C on order.  If they have similar protocols, this tool will be updated to support them.
