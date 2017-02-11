#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The purpose of this python code is to make a connection with the F4S/D series controller
# manufactured by Watlow (Winona, Minnesota, USA) with the aim of developing a semi-automatic
# data-collection under predefined temperature profile. 
# The manual of the temperature chambers and controller can be found in the Manual folder. 




# MinimalModbus is an easy-to-use Python module for talking to instruments (slaves)
# from a computer (master) using the Modbus protocol. 
# The documentation can be found: https://minimalmodbus.readthedocs.org.
# The GitHub source code can be found: https://github.com/pyhys/minimalmodbus

import minimalmodbus
import time


# Connecting the computer interface with the chamber through USB

minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
instrument = minimalmodbus.Instrument('/dev/tty.usbserial-FTVT25YW', 1,mode='rtu') 
instrument.serial.baudrate = 9600

# Defining the temperature measurements:

temp_values=[5,10,15,20,23,30,40,50,60,70,80]

# This sets the temperature at predefined temp_values.
# The heating/cooling ramp can be controlled but in this specific recipe since the ramping
# time is infinitesimal as compare to the overall temperature profile, it was left as default
# value (i.e. the shortest time that it takes to get to next pre-set temperature.
 


for i in temp_values:
    print i
    instrument = minimalmodbus.Instrument('/dev/tty.usbserial-FTVT25YW', 1,mode='rtu') 
    instrument.serial.baudrate = 9600
    temperature_set=instrument.write_register(300, i, 1) # sets the temperature
    time.sleep(60)					# this is the soaking time, as default 60 min.
    
    # In case you are measuring a sensor signal of a device inside chamber,
    # enter the python code for collecting data from the device over here.
    
    temperature_actual= instrument.read_register(100, 1) # this measures the actual temp.
    print temperature_actual

