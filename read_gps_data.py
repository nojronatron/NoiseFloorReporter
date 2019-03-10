# Goal: Read GPS puck serial data
# Actual output: Writes parsed GPGGA NMEA Lat & Long to 'beacon_data.txt'
# GPS puck used for creation & testing is a BU-353S4; COMn 4800 baud, 8 data, No parity, 1 stop, xon/xoff
#   Example: 47°48'21.16", -122°15'5.75", 1/25/2019 15:56:13, 14240000, -116.5, 1.0, 10.0
#   Headers: LatDD, LongDD, Date(local), Time(24local), Dial Hz, Signal dB, SNR dB, SNR_Weight
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
# 10-Mar-2019:
#     Removed dead/comment code
#     Added snr_weight variable - an indicator of LEVEL OF NOISE (low noise = more negative; more noise = more positive)
#     Enhanced get_serial_nmea() to interrogate the GPS Serial Port and return the data on its own or via input from a caller

import sys
import string
import serial
from pynmea import nmea

def get_serial_nmea(port_num=0):
    gpgga = nmea.GPGGA()
    port_num = 1 if port_num == 0 else port_num
    trying = True
    while trying:
        com_port = 'COM{0}'.format(port_num)
        try:
            # print('attempting com_port {0}'.format(com_port))
            ser = serial.Serial(
                port=str(com_port),  # Ports 1 thru 10 will be checked and nmea data returned if GPS Puck found
                baudrate=4800,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            test_data = ser.readline()
            if test_data:
                trying = False
        except serial.serialutil.SerialException as e:
            # sys.stderr.write('Could not open serial port {}: {}\n'.format(port_num, e))
            if port_num >= 10:
                sys.exit(1)
        port_num += 1
    # print('com_port is now: {0}'.format(com_port))

    working = True
    while working:
        data = ser.readline()
        str_data = str(data)
        if 'GPGGA' in str_data:  # method for parsing the sentence
            gpgga.parse(str_data)
            lats = str(gpgga.parts[2])
            longs = str(gpgga.parts[4])
            time_stamp = str(gpgga.parts[1])  # not currently used by this script
            alt = str(gpgga.parts[9])  # not currently used by this script
            ser.close()
            latitude_str = str(lats) + 'N' if str(gpgga.parts[3]).lower() == 'n' else str(lats) + 'S'
            longitude_str = str(longs) + 'E' if str(gpgga.parts[4]).lower() == 'e' else str(longs) + 'W'
            # gps_data_str = latitude_str + ',' + longitude_str
            # return gps_data_str, com_port
            return latitude_str + ',' + longitude_str, com_port


def log_the_data(gps_dm_data):
    with open(file='..\SDRuno_PWRSNR.csv') as csv_file:
        result = ''
        if csv_file.readable():
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
            result_bits = result.split(',')
            snr_weight = float(result_bits[3]) * -10
            beacon_data = gps_dm_data + ', ' + result.replace('\n', '') + ', ' + str(snr_weight) + '\n'
            print(beacon_data)
            beacon_log.write(beacon_data)


def dms2dd(DMS):
    DMS.strip("'")
    dms_split = str(DMS).split(',')  # ['4744.00N', '12219.73W']
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


DMS_data, comport = get_serial_nmea()
DD_data = dms2dd(DMS_data)
DD_DMS_data = DMS_data + ', ' + DD_data
log_the_data(DD_DMS_data)
