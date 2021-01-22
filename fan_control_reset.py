# -*- coding: utf-8 -*-
#
# Author: ATRedline
# More information: https://github.com/ATRedline/ESP32_Fan_Control
# Version: 1.1

import os, sys, time

fc_path = os.path.abspath(sys.argv[0]).rfind('\\')
fc_path = os.path.abspath(sys.argv[0])[:fc_path+1]

if not os.path.isfile(fc_path + r'fan_control_reset.cfg'):
    with open(fc_path+r'fan_control_reset.cfg', 'wb') as file:
        file.write(b'10');

with open(fc_path+r'fan_control_reset.cfg', 'rb') as file:
    try:
        delay = int(file.read())
    except:
        delay = 10

time.sleep(delay)
os.spawnv(os.P_DETACH, fc_path + r'fan_control.exe', [r'fan_control.exe'])