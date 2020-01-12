# rdserialtool - RDTech UM/DPS/RD series device interface tool

*This program is currently in an early stage and could change significantly.*

This program provides monitor, control and configuration access to [RDTech (RuiDeng, Riden)](https://rdtech.aliexpress.com/store/923042) UM, DPS and RD series devices.

The [UM24C](https://www.aliexpress.com/item/RD-UM24-UM24C-for-APP-USB-2-0-LCD-Display-Voltmeter-ammeter-battery-charge-voltage-current/32845522857.html), [UM25C](https://www.aliexpress.com/store/product/RD-UM25-UM25C-for-APP-USB-2-0-Type-C-LCD-Voltmeter-ammeter-voltage-current-meter/923042_32855845265.html) and [UM34C](https://www.aliexpress.com/store/product/RD-UM34-UM34C-for-APP-USB-3-0-Type-C-DC-Voltmeter-ammeter-voltage-current-meter/923042_32880908871.html) are low-cost USB pass-through power measurement devices, and support a decent number of collection features, as well as full control via Bluetooth.  (The non-C versions of these devices support the same features as the C versions, but without Bluetooth control.)

The [DPS series](https://rdtech.aliexpress.com/store/923042) are programmable DC-DC power supplies, and many devices in the series support external communication via the [Modbus](https://en.wikipedia.org/wiki/Modbus) RTU serial protocol over USB or Bluetooth.

The RD6006 is a logical continuation of the DPS series and also uses Modbus communication, but the registers are incompatible with previous DPS series, so "RD" is treated as a separate series.

## Compatibility

 * UM24C, UM25C and UM34C support is complete and tested.
 * DPS5005 support is complete and tested.  Other devices in the DPS series (DPS3005, DPS5015, DPS5020, DPS8005, DPH5005) should perform identically.  (Status reports and bugs welcome.)
 * RD6006 has basic support and testing.  Reading and writing most states work.
 * Tested under Python 3.6, but should work with 3.4 or later.
 * Linux: Tested fine with both PyBluez (direct) and pyserial (e.g. /dev/rfcomm0 via ```rfcomm bind```), as well as direct USB serial (e.g. /dev/ttyUSB0) on DPS devices.
 * Windows: Tested fine with pyserial (e.g. COM4 as set up automatically by Windows).  Author could not get PyBluez compiled/installed.
 * MacOS: When using pyserial (e.g. /dev/cu.UM24C-Port as set up automatically by MacOS), writes to the device would succeed (e.g. 0xf2 to rotate the screen on UM series), but reads from the device never arrive.  Author could not get PyBluez compiled/installed.

## Setup

rdserialtool requires Python 3, and [PyBluez](https://pypi.org/project/PyBluez/) and/or [pyserial](https://pypi.org/project/pyserial/) modules, depending on which method you use to connect.  Installation varies by operating system, but on Debian/Ubuntu, these are available via the python3-pybluez and python3-serial packages, respectively.

To install rdserialtool:

```
$ sudo python3 setup.py install
```

rdserialtool may also be run directly from its source directory without installation.

## Bluetooth setup

Varies by operating system.  If the pairing procedure asks for a PIN, enter 1234.

For command-line installation on Linux:

```
$ bluetoothctl
Agent registered
[bluetooth]# scan on
Discovery started
[NEW] Device 00:90:72:56:98:D7 UM24C
[CHG] Device 00:90:72:56:98:D7 RSSI: -60
[bluetooth]# pair 00:90:72:56:98:D7
Attempting to pair with 00:90:72:56:98:D7
[CHG] Device 00:90:72:56:98:D7 Connected: yes
Request PIN code
[UM241m[agent] Enter PIN code: 1234
[CHG] Device 00:90:72:56:98:D7 UUIDs: 00001101-0000-1000-8000-00805f9b34fb
[CHG] Device 00:90:72:56:98:D7 ServicesResolved: yes
[CHG] Device 00:90:72:56:98:D7 Paired: yes
Pairing successful
[bluetooth]# trust 00:90:72:56:98:D7
[CHG] Device 00:90:72:56:98:D7 Trusted: yes
Changing 00:90:72:56:98:D7 trust succeeded
[bluetooth]# exit
Agent unregistered
```

Device MAC address will vary.  Again, the PIN for the device is 1234.

If you then want to use rdserialtool via direct serial, bind it via rfcomm:

```
$ sudo rfcomm bind 0 00:90:72:56:98:D7
```

## Usage

A number of options common to device access are available to all commands; see:

```
$ rdserialtool --help
```

After the common options, a command is required (commands available are in ```--help``` above).  For example, to get device information from a UM24C via PyBluez:

```
$ rdserialtool --device=um24c --bluetooth-address=00:90:72:56:98:D7
```

Or via pyserial:

```
$ rdserialtool --device=um24c --serial-device=/dev/rfcomm0
```

To turn the output on for a DPS device:

```
$ rdserialtool --device=dps --bluetooth-address=00:BA:68:00:47:3A --on
```

## Example

```
$ rdserialtool --device=um25c --bluetooth-address=00:15:A6:00:36:2F
rdserialtool
Copyright (C) 2019 Ryan Finnie

Connecting to UM25C 00:15:A6:00:36:2F
Connection established

USB: 5.062V, 0.1146A,  0.580W,   44.1Ω
Data:  0.01V(+),  0.00V(-), charging mode: DCP 1.5A
Recording (off):    0.000Ah,    0.000Wh,      0 sec at >= 0.13A
Data groups:
    *0:    0.001Ah,    0.009Wh       5:    0.000Ah,    0.000Wh
     1:    0.000Ah,    0.000Wh       6:    0.000Ah,    0.000Wh
     2:    0.000Ah,    0.000Wh       7:    0.000Ah,    0.000Wh
     3:    0.000Ah,    0.000Wh       8:    0.000Ah,    0.000Wh
     4:    0.000Ah,    0.000Wh       9:    0.000Ah,    0.000Wh
UM25C, temperature:  25C ( 78F)
Screen: 1/6, brightness: 4/5, timeout: 2 min
Collection time: 2019-02-23 22:53:08.468732
```

```
$ rdserialtool --device=dps --bluetooth-address=00:BA:68:00:47:3A
rdserialtool
Copyright (C) 2019 Ryan Finnie

Connecting to DPS 00:BA:68:00:47:3A
Connection established

Setting:  5.00V,  5.100A (CV)
Output (on) :  5.00V,  0.15A,   0.07W
Input: 19.30V, protection: good
Brightness: 4/5, key lock: off
Model: 5005, firmware: 14
Collection time: 2019-02-23 22:55:24.721946
```

```
$ rdserialtool --device=rd --serial-device=/dev/ttyUSB0 --baud=115200
rdserialtool
Copyright (C) 2019 Ryan Finnie

Connecting to RD /dev/ttyUSB0
Connection established

Setting: 15.00V,  0.998A (CV)
Output (on) : 14.99V,  0.14A,   0.20W
Input: 50.15V, protection: good
Brightness: 4/5, key lock: off
Model: 60062, firmware: 125, serial: 5403
Collection time: 2019-12-28 21:16:07.114146
```
## GUI

To enable the gui 

```
rdserialtool --device=rd --serial-device=/dev/ttyUSB0 --baud=115200 --gui
```

To make the gui stay on top of other windows 

```
rdserialtool --device=rd --serial-device=/dev/ttyUSB0 --baud=115200 --gui --gui-on-top
```


![GUI in operation](/gui.gif)


## About

Copyright (C) 2019 Ryan Finnie

GUI Copyright (C) 2020 Darren Jones

> This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
>
> This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

This tool is not affiliated with or endorsed by RDTech.

## See also

* [RDTech UM series](https://sigrok.org/wiki/RDTech_UM_series) on the sigrok wiki, which contains a lot of information and reverse engineering of the protocol used on these devices.
* [DPS5005 communication protocol](https://www.mediafire.com/folder/3iogirsx1s0vp/DPS_communication_upper_computer#napmdzd4qt2dt) and Android/Windows software, from the manufacturer.
* [opendps](https://github.com/kanflo/opendps), a replacement firmware package for the DPS5005.  (Incompatible with rdserialtool, as opendps uses its own communication interface.)
