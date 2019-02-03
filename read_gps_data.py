# Goal: Read GPS puck serial data
# Actual output: Writes parsed GPGGA NMEA Lat & Long to 'beacon_data.txt'
# GPS puck used for creation & testing is a BU-353S4; COMn 4800 baud, 8 data, No parity, 1 stop, xon/xoff
#   Example: 47°48'21.16", -122°15'5.75", 1/25/2019 15:56:13, 14240000, -116.5, 1.0
#   Headers: LatDD, LongDD, Date(local), Time(24local), Dial Hz, Signal dB, SNR dB
#
# How to use: You will need to run this script from a trigger ex: Scheduled Task (date, time, etc) python.exe -s 'read_gps_data.py'
# Note: If you try to use this file in Windows when GPS is in use by APRS (ex: Direwolf) it will fail.
# Note: In Linux/Raspian, GPS can be shared using GPSD; enabling shared use with APRS (ex: Direwolf).
#
# Reference: https://stackoverflow.com/
# Portions of this code from Amal G Jose for parsing GPGGA data to lat/long/elev/time output
# python.exe -m pip install pyserial
# python.exe -m pip install pynmea
#
# 1-Feb-2019: Many updates to fix path issues and correct output and logging format
#     also commented-out various non-ascii characters degree, minutes, and seconds signs

import sys
import string
import serial
from pynmea import nmea

def get_serial_nmea():
    gpgga = nmea.GPGGA()

    try:
        # TODO: Make port and baudrate arguments to script execution
        ser = serial.Serial(
            port='COM8',  # Edit com port to match your GPS receiver COM number e.g. COM3 or COM8
            baudrate=4800,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
    except serial.SerialException as e:
        sys.stderr.write('Could not open serial port {}: {}\n'.format(ser.name, e))
        ser.close()
        sys.exit(1)

    working = True
    while working:
        data = ser.readline()
        str_data = str(data)
        if 'GPGGA' in str_data:
            # method for parsing the sentence
            gpgga.parse(str_data)
            # print('gpgga_parts: {0}'.format(gpgga.parts))
            lats = str(gpgga.parts[2])
            longs = str(gpgga.parts[4])
            # print('lats, longs: {0}, {1}'.format(lats, longs))
            time_stamp = str(gpgga.parts[1])
            alt = str(gpgga.parts[9])
            ser.close()
            # lat_deg = lats[0:2]
            # print('lat_deg: {0}'.format(lat_deg))
            # lat_mins = lats[2:4]
            # print('lat_mins: {0}'.format(lat_mins))
            # lat_secs = int(round(float(lats[5:])*60/10000, 0))
            # print('lat_secs: {0}'.format(lat_secs))
            latitude_str = str(lats) + 'N' if str(gpgga.parts[3]).lower() == 'n' else str(lats) + 'S'
            # latitude_str = lat_deg + ' ' + lat_mins + '.' + str(lat_secs) + ' N'
            # latitude_str = lat_deg + u'\N{DEGREE SIGN}' + lat_mins + string.printable[68] + str(lat_secs) + string.printable[63]
            # print('latitude_str: {0}'.format(latitude_str))
            # longs_deg = longs[0:3]
            # print('longs_deg: {0}'.format(longs_deg))
            # longs_mins = longs[3:5]
            # print('longs_mins: {0}'.format(longs_mins))
            # longs_secs = int(round(float(longs[6:])*60/10000, 0))
            # print('longs_secs: {0}'.format(longs_secs))
            longitude_str = str(longs) + 'E' if str(gpgga.parts[4]).lower() == 'e' else str(longs) + 'W'
            # if str(gpgga.parts[5]) == 'W':
                # longitude_str = '-' + longs_deg + ' ' + longs_mins + '.' + str(longs_secs) + ' W'
                # longitude_str = '-' + longs_deg + u'\N{DEGREE SIGN}' + longs_mins + string.printable[68] + str(longs_secs) + string.printable[63]
            # else:
                # longitude_str = longs_deg + ' ' + longs_mins + '.' + str(longs_secs) + ' E'
                # longitude_str = longs_deg + u'\N{DEGREE SIGN}' + longs_mins + string.printable[68] + str(longs_secs) + string.printable[63]
            gps_data_str = latitude_str + ',' + longitude_str
            return gps_data_str


def log_the_data(gps_dm_data):
    with open(file='..\SDRuno_PWRSNR.csv') as csv_file:
        result = ''
        if csv_file.readable():
            header = csv_file.readline()
            while True:
                read_data = csv_file.readline()
                if len(read_data) >= 5:
                    result = read_data
                else:
                    break
        else:
            result = "File not readable"
    with open('beacon_data.txt', 'a+') as beacon_log:
        if 'File not readable' in result:
            print(result)
            return False
        else:
            result.strip('\\n')
            beacon_data = gps_dm_data + ', ' + result + '\n'
            print(beacon_data)
            beacon_log.write(beacon_data)


def dms2dd(DMS):
    DMS.strip("'")
    dms_split = str(DMS).split(',')  # ['4744.00N', '12219.73W']
    # print('dms_split: {0}'.format(dms_split))
    LATdms = str(dms_split[0])  # '4744.00N'
    LONdms = str(dms_split[1])  # '12219.73W'
    LATdd = int(LATdms[0:2]) + (int(LATdms[2:4]) / 60) + (int(LATdms[5:7]) / 3600)  # LATdd: 47.733333333333334
    LONdd = int(LONdms[0:3]) + (int(LONdms[3:5]) / 60) + (int(LONdms[6:8]) / 3600)  # LONdd: 122.33694444444444
    rnd_LATdd = round(LATdd, 4)
    rnd_LONdd = round(LONdd, 4)
    if str(LATdms[-1]).lower() == 's':
        str_LATdd = '{0}{1}'.format('-', str(rnd_LATdd))
    else:
        str_LATdd = str(rnd_LATdd)
    if str(LONdms[-1]).lower() == 'w':
        str_LONdd = '{0}{1}'.format('-', str(rnd_LONdd))
    else:
        str_LONdd = str(rnd_LONdd)
    return '{0},{1}'.format(str_LATdd, str_LONdd)

            
DMS_data = get_serial_nmea()
DD_data = dms2dd(DMS_data)
DD_DMS_data = DMS_data + ', ' + DD_data
log_the_data(DD_DMS_data)
