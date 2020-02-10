# -*- coding: utf-8 -*-
#
# Author: ATRedline
#
# Version: 1.0
#
# This is reset script for ESP32 Fan Control. ESP32 Fan control need to be compiled to fan_control.exe

import os
import time

time.sleep(5)
os.spawnv(os.P_DETACH, os.getcwd()+r'\fan_control.exe', ['-'])