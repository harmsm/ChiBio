######### Chi.Bio Operating System V1.0 #########

#Import required python packages
import os
import json
import time
import math
from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import numpy as np
from datetime import datetime
import Adafruit_GPIO.I2C as I2C
import Adafruit_BBIO.GPIO as GPIO
import time
import simplejson
import copy
import csv
import smbus2 as smbus


application = Flask(__name__)
application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #Try this https://stackoverflow.com/questions/23112316/using-flask-how-do-i-modify-the-cache-control-header-for-all-output/23115561#23115561

lock = Lock()
        
# Initialise data structures.

class SystemConfiguration:
    """
    Class holds configuration of system hardware.
    """
    
    def __init__(self,config_file):

        self._config_file = config_file

        with open(self._config_file) as f:
            config = json.load(f)

        to_replace = ["ONL","ONH","OFFL","OFFH"]
        for k in config["sysItems"].keys():
            
            try:
                key_list = config["sysItems"][k].keys()
            except AttributeError:
                continue

            for m in key_list:
                if m in to_replace:
                    config["sysItems"][k][m] = int(config["sysItems"][k][m],16)

                try:
                    nested_key_list = config["sysItems"][k][m].keys()
                except AttributeError:
                    continue

                for n in nested_key_list:
                    if n in to_replace: 
                        config["sysItems"][k][m][n] = int(config["sysItems"][k][m][n],16)

        for M in ['M1','M2','M3','M4','M5','M6','M7']:
            config["sysData"][M] = copy.deepcopy(config["sysData"]["M0"])
            config["sysDevices"][M] = copy.deepcopy(config["sysDevices"]["M0"])

        self._config = config

    @property
    def sysData(self):
        return self._config["sysData"]
    
    @property
    def sysDevices(self):
        return self._config["sysDevices"]
    
    @property
    def sysItems(self):
        return self._config["sysItems"]

                



# class SystemConfiguration:

#     def __init__(self):

#         #system.sysData is a structure created for each device and contains the setup / measured data related to that device during an experiment. All of this information is passed into the user interface during an experiment.
#         self.sysData = {'M0' : {
#         'UIDevice' : 'M0',
#         'present' : 0,
#         'presentDevices' : { 'M0' : 0,'M1' : 0,'M2' : 0,'M3' : 0,'M4' : 0,'M5' : 0,'M6' : 0,'M7' : 0},
#         'Version' : {'value' : 'Turbidostat V3.0'},
#         'DeviceID' : '',
#         'time' : {'record' : []},
#         'LEDA' : {'WL' : '395', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDB' : {'WL' : '457', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDC' : {'WL' : '500', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDD' : {'WL' : '523', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDE' : {'WL' : '595', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDF' : {'WL' : '623', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LEDG' : {'WL' : '6500K', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'LASER650' : {'name' : 'LASER650', 'default': 0.5, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'UV' : {'WL' : 'UV', 'default': 0.5, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
#         'Heat' : {'default': 0.0, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0,'record' : []},
#         'Thermostat' : {'default': 37.0, 'target' : 0.0, 'max': 50.0, 'min' : 0.0,'ON' : 0,'record' : [],'cycleTime' : 30.0, 'Integral' : 0.0,'last' : -1},
#         'Experiment' : {'indicator' : 'USR0', 'startTime' : 'Waiting', 'startTimeRaw' : 0, 'ON' : 0,'cycles' : 0, 'cycleTime' : 60.0,'threadCount' : 0},
#         'Terminal' : {'text' : ''},
#         'AS7341' : {
#                 'spectrum' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0, 'NIR' : 0,'DARK' : 0,'ExtGPIO' : 0, 'ExtINT' : 0, 'FLICKER' : 0},
#                 'channels' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0, 'NIR' : 0,'DARK' : 0,'ExtGPIO' : 0, 'ExtINT' : 0, 'FLICKER' : 0},
#                 'current' : {'ADC0': 0,'ADC1': 0,'ADC2': 0,'ADC3': 0,'ADC4': 0,'ADC5' : 0}},
#         'ThermometerInternal' : {'current' : 0.0,'record' : []},
#         'ThermometerExternal' : {'current' : 0.0,'record' : []},
#         'ThermometerIR' : {'current' : 0.0,'record' : []},
#         'OD' :  {'current' : 0.0,'target' : 0.5,'default' : 0.5,'max': 10, 'min' : 0,'record' : [],'targetrecord' : [],'Measuring' : 0, 'ON' : 0,'Integral' : 0.0,'Integral2' : 0.0,'device' : 'LASER650'},
#         'OD0' : {'target' : 0.0,'raw' : 0.0,'max' : 100000.0,'min': 0.0,'LASERb' : 1.833 ,'LASERa' : 0.226, 'LEDFa' : 0.673, 'LEDAa' : 7.0  },
#         'Chemostat' : {'ON' : 0, 'p1' : 0.0, 'p2' : 0.1},
#         'Zigzag': {'ON' : 0, 'Zig' : 0.04,'target' : 0.0,'SwitchPoint' : 0},
#         'GrowthRate': {'current' : 0.0,'record' : [],'default' : 2.0},
#         'Volume' : {'target' : 20.0,'max' : 50.0, 'min' : 0.0,'ON' : 0},
#         'Pump1' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
#         'Pump2' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
#         'Pump3' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
#         'Pump4' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
#         'Stir' :  {'target' : 0.0,'default' : 0.5,'max': 1.0, 'min' : 0.0, 'ON' : 0},
#         'Light' :  {'target' : 0.0,'default' : 0.5,'max': 1.0, 'min' : 0.0, 'ON' : 0, 'Excite' : 'LEDD', 'record' : []},
#         'Custom' :  {'Status' : 0.0,'default' : 0.0,'Program': 'C1', 'ON' : 0,'param1' : 0, 'param2' : 0, 'param3' : 0.0, 'record' : []},
#         'FP1' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
#         'FP2' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
#         'FP3' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
#         'biofilm' : {'LEDA' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDB' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDC' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDD' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDE' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDF' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LEDG' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
#                         'LASER650' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0}}
#         }}



#         #system.sysDevices is unique to each device and is responsible for storing information required for the digital communications, and various automation funtions. These values are stored outside system.sysData since they are not passable into the HTML interface using the jsonify package.        
#         self.sysDevices = {'M0' : {
#             'AS7341' : {'device' : 0},
#             'ThermometerInternal' : {'device' : 0},
#             'ThermometerExternal' : {'device' : 0},
#             'ThermometerIR' : {'device' : 0,'address' :0},
#             'DAC' : {'device' : 0},
#             'Pumps' : {'device' : 0,'startup' : 0, 'frequency' : 0},
#             'PWM' : {'device' : 0,'startup' : 0, 'frequency' : 0},
#             'Pump1' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
#             'Pump2' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
#             'Pump3' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
#             'Pump4' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
#             'Experiment' : {'thread' : 0},
#             'Thermostat' : {'thread' : 0,'threadCount' : 0},
            
#         }}


#         for M in ['M1','M2','M3','M4','M5','M6','M7']:
#                 self.sysData[M]=copy.deepcopy(self.sysData['M0'])
#                 self.sysDevices[M]=copy.deepcopy(self.sysDevices['M0'])
                

#         #system.sysItems stores information about digital addresses which is used as a reference for all devices.        
#         self.system.sysItems = {
#             'DAC' : {'LEDA' : '00000100','LEDB' : '00000000','LEDC' : '00000110','LEDD' : '00000001','LEDE' : '00000101','LEDF' : '00000011','LEDG' : '00000010','LASER650' : '00000111'},
#             'Multiplexer' : {'device' : 0 , 'M0' : '00000001','M1' : '00000010','M2' : '00000100','M3' : '00001000','M4' : '00010000','M5' : '00100000','M6' : '01000000','M7' : '10000000'},
#             'UIDevice' : 'M0',
#             'Watchdog' : {'pin' : 'P8_11','thread' : 0,'ON' : 1},
#             'FailCount' : 0,
#             'All' : {'ONL' : 0xFA, 'ONH' : 0xFB, 'OFFL' : 0xFC, 'OFFH' : 0xFD},
#             'Stir' : {'ONL' : 0x06, 'ONH' : 0x07, 'OFFL' : 0x08, 'OFFH' : 0x09},
#             'Heat' : {'ONL' : 0x3E, 'ONH' : 0x3F, 'OFFL' : 0x40, 'OFFH' : 0x41},
#             'UV' : {'ONL' : 0x42, 'ONH' : 0x43, 'OFFL' : 0x44, 'OFFH' : 0x45},
#             'LEDA' : {'ONL' : 0x0E, 'ONH' : 0x0F, 'OFFL' : 0x10, 'OFFH' : 0x11},
#             'LEDB' : {'ONL' : 0x16, 'ONH' : 0x17, 'OFFL' : 0x18, 'OFFH' : 0x19},
#             'LEDC' : {'ONL' : 0x0A, 'ONH' : 0x0B, 'OFFL' : 0x0C, 'OFFH' : 0x0D},
#             'LEDD' : {'ONL' : 0x1A, 'ONH' : 0x1B, 'OFFL' : 0x1C, 'OFFH' : 0x1D},
#             'LEDE' : {'ONL' : 0x22, 'ONH' : 0x23, 'OFFL' : 0x24, 'OFFH' : 0x25},
#             'LEDF' : {'ONL' : 0x1E, 'ONH' : 0x1F, 'OFFL' : 0x20, 'OFFH' : 0x21},
#             'LEDG' : {'ONL' : 0x12, 'ONH' : 0x13, 'OFFL' : 0x14, 'OFFH' : 0x15},
#             'Pump1' : {
#                 'In1' : {'ONL' : 0x06, 'ONH' : 0x07, 'OFFL' : 0x08, 'OFFH' : 0x09},
#                 'In2' : {'ONL' : 0x0A, 'ONH' : 0x0B, 'OFFL' : 0x0C, 'OFFH' : 0x0D},
#             },
#             'Pump2' : {
#                 'In1' : {'ONL' : 0x0E, 'ONH' : 0x0F, 'OFFL' : 0x10, 'OFFH' : 0x11},
#                 'In2' : {'ONL' : 0x12, 'ONH' : 0x13, 'OFFL' : 0x14, 'OFFH' : 0x15},
#             },
#             'Pump3' : {
#                 'In1' : {'ONL' : 0x16, 'ONH' : 0x17, 'OFFL' : 0x18, 'OFFH' : 0x19},
#                 'In2' : {'ONL' : 0x1A, 'ONH' : 0x1B, 'OFFL' : 0x1C, 'OFFH' : 0x1D},
#             },
#             'Pump4' : {
#                 'In1' : {'ONL' : 0x1E, 'ONH' : 0x1F, 'OFFL' : 0x20, 'OFFH' : 0x21},
#                 'In2' : {'ONL' : 0x22, 'ONH' : 0x23, 'OFFL' : 0x24, 'OFFH' : 0x25},
#             },
#             'AS7341' : {
#                 '0x00' : {'A' : 'nm470', 'B' : 'U'},
#                 '0x01' : {'A' : 'U', 'B' : 'nm410'},
#                 '0x02' : {'A' : 'U', 'B' : 'U'},
#                 '0x03' : {'A' : 'nm670', 'B' : 'U'},
#                 '0x04' : {'A' : 'U', 'B' : 'nm583'},
#                 '0x05' : {'A' : 'nm510', 'B' : 'nm440'},
#                 '0x06' : {'A' : 'nm550', 'B' : 'U'},
#                 '0x07' : {'A' : 'U', 'B' : 'nm620'},
#                 '0x08' : {'A' : 'CLEAR', 'B' : 'U'},
#                 '0x09' : {'A' : 'nm550', 'B' : 'U'},
#                 '0x0A' : {'A' : 'U', 'B' : 'nm620'},
#                 '0x0B' : {'A' : 'U', 'B' : 'U'},
#                 '0x0C' : {'A' : 'nm440', 'B' : 'U'},
#                 '0x0D' : {'A' : 'U', 'B' : 'nm510'},
#                 '0x0E' : {'A' : 'nm583', 'B' : 'nm670'},
#                 '0x0F' : {'A' : 'nm470', 'B' : 'U'},
#                 '0x10' : {'A' : 'ExtGPIO', 'B' : 'nm410'},
#                 '0x11' : {'A' : 'CLEAR', 'B' : 'ExtINT'},
#                 '0x12' : {'A' : 'DARK', 'B' : 'U'},
#                 '0x13' : {'A' : 'FLICKER', 'B' : 'NIR'},
#             }
#         }
   
system = SystemConfiguration("config.json")

# This section of code is responsible for the watchdog circuit. The circuit is implemented in hardware on the control computer, and requires the watchdog pin be toggled low->high each second, otherwise it will power down all connected devices. This section is therefore critical to operation of the device.
def runWatchdog():  
    #Watchdog timing function which continually runs in a thread.
    global system
    if (system.sysItems['Watchdog']['ON']==1):
        #system.sysItems['Watchdog']['thread']
        toggleWatchdog()
        time.sleep(0.15)
        system.sysItems['Watchdog']['thread']=Thread(target = runWatchdog, args=())
        system.sysItems['Watchdog']['thread'].setDaemon(True)
        system.sysItems['Watchdog']['thread'].start()

def toggleWatchdog():
    #Toggle the watchdog
    global system
    GPIO.output(system.sysItems['Watchdog']['pin'], GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(system.sysItems['Watchdog']['pin'], GPIO.LOW)
    


GPIO.setup(system.sysItems['Watchdog']['pin'], GPIO.OUT)
print(str(datetime.now()) + ' Starting watchdog')
system.sysItems['Watchdog']['thread']=Thread(target = runWatchdog, args=())
system.sysItems['Watchdog']['thread'].setDaemon(True)
system.sysItems['Watchdog']['thread'].start()
GPIO.setup('P8_15', GPIO.OUT) #This output connects to the RESET pin on the I2C Multiplexer.
GPIO.output('P8_15', GPIO.HIGH)
GPIO.setup('P8_17', GPIO.OUT) #This output connects to D input of the D-Latch 
GPIO.output('P8_17', GPIO.HIGH)


def initialise(M):

    # Function that initialises all parameters / clears stored values for a
    # given device. If you want to record/add values to system.sysData,
    # recommend adding an initialisation line in here.
    
    global system

    for LED in ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG']:
        system.sysData[M][LED]['target']=system.sysData[M][LED]['default']
        system.sysData[M][LED]['ON']=0
    
    system.sysData[M]['UV']['target']=system.sysData[M]['UV']['default']
    system.sysData[M]['UV']['ON']=0
    
    system.sysData[M]['LASER650']['target']=system.sysData[M]['LASER650']['default']
    system.sysData[M]['LASER650']['ON']=0
    
    FP = 'FP1'
    system.sysData[M][FP]['ON']=0
    system.sysData[M][FP]['LED']="LEDB"
    system.sysData[M][FP]['Base']=0
    system.sysData[M][FP]['Emit1']=0
    system.sysData[M][FP]['Emit2']=0
    system.sysData[M][FP]['BaseBand']="CLEAR"
    system.sysData[M][FP]['Emit1Band']="nm510"
    system.sysData[M][FP]['Emit2Band']="nm550"
    system.sysData[M][FP]['Gain']="x10"
    system.sysData[M][FP]['BaseRecord']=[]
    system.sysData[M][FP]['Emit1Record']=[]
    system.sysData[M][FP]['Emit2Record']=[]
    FP = 'FP2'
    system.sysData[M][FP]['ON']=0
    system.sysData[M][FP]['LED']="LEDD"
    system.sysData[M][FP]['Base']=0
    system.sysData[M][FP]['Emit1']=0
    system.sysData[M][FP]['Emit2']=0
    system.sysData[M][FP]['BaseBand']="CLEAR"
    system.sysData[M][FP]['Emit1Band']="nm583"
    system.sysData[M][FP]['Emit2Band']="nm620"
    system.sysData[M][FP]['BaseRecord']=[]
    system.sysData[M][FP]['Emit1Record']=[]
    system.sysData[M][FP]['Emit2Record']=[]
    system.sysData[M][FP]['Gain']="x10"
    FP='FP3'
    system.sysData[M][FP]['ON']=0
    system.sysData[M][FP]['LED']="LEDE"
    system.sysData[M][FP]['Base']=0
    system.sysData[M][FP]['Emit1']=0
    system.sysData[M][FP]['Emit2']=0
    system.sysData[M][FP]['BaseBand']="CLEAR"
    system.sysData[M][FP]['Emit1Band']="nm620"
    system.sysData[M][FP]['Emit2Band']="nm670"
    system.sysData[M][FP]['BaseRecord']=[]
    system.sysData[M][FP]['Emit1Record']=[]
    system.sysData[M][FP]['Emit2Record']=[]
    system.sysData[M][FP]['Gain']="x10"
 
    for PUMP in ['Pump1','Pump2','Pump3','Pump4']:
        system.sysData[M][PUMP]['default']=0.0
        system.sysData[M][PUMP]['target']=system.sysData[M][PUMP]['default']
        system.sysData[M][PUMP]['ON']=0
        system.sysData[M][PUMP]['direction']=1.0
        system.sysDevices[M][PUMP]['threadCount']=0
        system.sysDevices[M][PUMP]['active']=0
    
    
    system.sysData[M]['Heat']['default']=0
    system.sysData[M]['Heat']['target']=system.sysData[M]['Heat']['default']
    system.sysData[M]['Heat']['ON']=0

    system.sysData[M]['Thermostat']['default']=37.0
    system.sysData[M]['Thermostat']['target']=system.sysData[M]['Thermostat']['default']
    system.sysData[M]['Thermostat']['ON']=0
    system.sysData[M]['Thermostat']['Integral']=0
    system.sysData[M]['Thermostat']['last']=-1

    system.sysData[M]['Stir']['target']=system.sysData[M]['Stir']['default']
    system.sysData[M]['Stir']['ON']=0
    
    system.sysData[M]['Light']['target']=system.sysData[M]['Light']['default']
    system.sysData[M]['Light']['ON']=0
    system.sysData[M]['Light']['Excite']='LEDD'
    
    system.sysData[M]['Custom']['Status']=system.sysData[M]['Custom']['default']
    system.sysData[M]['Custom']['ON']=0
    system.sysData[M]['Custom']['Program']='C1'
    
    system.sysData[M]['Custom']['param1']=0.0
    system.sysData[M]['Custom']['param2']=0.0
    system.sysData[M]['Custom']['param3']=0.0
    
    system.sysData[M]['OD']['current']=0.0
    system.sysData[M]['OD']['target']=system.sysData[M]['OD']['default']
    system.sysData[M]['OD0']['target']=65000.0
    system.sysData[M]['OD0']['raw']=65000.0
    system.sysData[M]['OD']['device']='LASER650'
    #system.sysData[M]['OD']['device']='LEDA'
    
    #if (M=='M0'):
    #    system.sysData[M]['OD']['device']='LEDA'
    
    
    system.sysData[M]['Volume']['target']=20.0
    
    clearTerminal(M)
    addTerminal(M,'System Initialised')
  
    system.sysData[M]['Experiment']['ON']=0
    system.sysData[M]['Experiment']['cycles']=0
    system.sysData[M]['Experiment']['threadCount']=0
    system.sysData[M]['Experiment']['startTime']=' Waiting '
    system.sysData[M]['Experiment']['startTimeRaw']=0
    system.sysData[M]['OD']['ON']=0
    system.sysData[M]['OD']['Measuring']=0
    system.sysData[M]['OD']['Integral']=0.0
    system.sysData[M]['OD']['Integral2']=0.0
    system.sysData[M]['Zigzag']['ON']=0
    system.sysData[M]['Zigzag']['target']=0.0
    system.sysData[M]['Zigzag']['SwitchPoint']=0
    system.sysData[M]['GrowthRate']['current']=system.sysData[M]['GrowthRate']['default']

    system.sysDevices[M]['Thermostat']['threadCount']=0

    channels=['nm410','nm440','nm470','nm510','nm550','nm583','nm620', 'nm670','CLEAR','NIR','DARK','ExtGPIO', 'ExtINT' , 'FLICKER']
    for channel in channels:
        system.sysData[M]['AS7341']['channels'][channel]=0
        system.sysData[M]['AS7341']['spectrum'][channel]=0
    DACS=['ADC0', 'ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
    for DAC in DACS:
        system.sysData[M]['AS7341']['current'][DAC]=0

    system.sysData[M]['ThermometerInternal']['current']=0.0
    system.sysData[M]['ThermometerExternal']['current']=0.0
    system.sysData[M]['ThermometerIR']['current']=0.0
 
    system.sysData[M]['time']['record']=[]
    system.sysData[M]['OD']['record']=[]
    system.sysData[M]['OD']['targetrecord']=[]
    system.sysData[M]['Pump1']['record']=[]
    system.sysData[M]['Pump2']['record']=[]
    system.sysData[M]['Pump3']['record']=[]
    system.sysData[M]['Pump4']['record']=[]
    system.sysData[M]['Heat']['record']=[]
    system.sysData[M]['Light']['record']=[]
    system.sysData[M]['ThermometerInternal']['record']=[]
    system.sysData[M]['ThermometerExternal']['record']=[]
    system.sysData[M]['ThermometerIR']['record']=[]
    system.sysData[M]['Thermostat']['record']=[]
	
    system.sysData[M]['GrowthRate']['record']=[]

    system.sysDevices[M]['ThermometerInternal']['device']=I2C.get_i2c_device(0x18,2) #Get Thermometer on Bus 2!!!
    system.sysDevices[M]['ThermometerExternal']['device']=I2C.get_i2c_device(0x1b,2) #Get Thermometer on Bus 2!!!
    system.sysDevices[M]['DAC']['device']=I2C.get_i2c_device(0x48,2) #Get DAC on Bus 2!!!
    system.sysDevices[M]['AS7341']['device']=I2C.get_i2c_device(0x39,2) #Get OD Chip on Bus 2!!!!!
    system.sysDevices[M]['Pumps']['device']=I2C.get_i2c_device(0x61,2) #Get OD Chip on Bus 2!!!!!
    system.sysDevices[M]['Pumps']['startup']=0
    system.sysDevices[M]['Pumps']['frequency']=0x1e #200Hz PWM frequency
    system.sysDevices[M]['PWM']['device']=I2C.get_i2c_device(0x60,2) #Get OD Chip on Bus 2!!!!!
    system.sysDevices[M]['PWM']['startup']=0
    system.sysDevices[M]['PWM']['frequency']=0x03# 0x14 = 300hz, 0x03 is 1526 Hz PWM frequency for fan/LEDs, maximum possible. Potentially dial this down if you are getting audible ringing in the device! 
    #There is a tradeoff between large frequencies which can make capacitors in the 6V power regulation oscillate audibly, and small frequencies which result in the number of LED "ON" cycles varying during measurements.
    system.sysDevices[M]['ThermometerIR']['device']=smbus.SMBus(bus=2) #Set up SMBus thermometer
    system.sysDevices[M]['ThermometerIR']['address']=0x5a 
    
    
    # # This section of commented code is used for testing I2C communication integrity.
    # system.sysData[M]['present']=1
    # getData=I2CCom(M,'ThermometerInternal',1,16,0x05,0,0)
    # i=0
    # while (1==1):
    #     i=i+1
    #     if (i%1000==1):
    #         print(str(i))
    #     system.sysDevices[M]['ThermometerInternal']['device'].readU8(int(0x05))
    # getData=I2CCom(M,which,1,16,0x05,0,0)
    

    scanDevices(M)
    if(system.sysData[M]['present'] == 1):
        turn_everything_off(M)
        print(str(datetime.now()) + " Initialised " + str(M) +', Device ID: ' + system.sysData[M]['DeviceID'])

    
    

def initialiseAll():
    # Initialisation function which runs at when software is started for the first time.
    system.sysItems['Multiplexer']['device'] = I2C.get_i2c_device(0x74,2) 
    system.sysItems['FailCount'] = 0
    time.sleep(2.0) # This wait is to allow the watchdog circuit to boot.
    print(str(datetime.now()) + ' Initialising devices')

    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
        initialise(M)
        print(system.sysItems['Watchdog']['ON'])
    scanDevices("all")
    
    
  
    
def turn_everything_off(M):
    """
    Turn every device off for turbidistat M.
    
    Parameters
    ----------
    M : str
        turbidistat identifier (M0, M1, etc.)    
    """

    to_turn_off = ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG',
                   'LASER650',
                   'Pump1','Pump2','Pump3','Pump4',
                   'Stir','Heat','UV']

    for turn_off in to_turn_off:
        system.sysData[M][turn_off]['ON'] = 0
        
    # Set all DAC Channels to zero 
    I2CCom(M,'DAC',0,8,int('00000000',2),int('00000000',2),0)

    # Turn PWM and Pumps to 0
    setPWM(M,'PWM',system.sysItems['All'],0,0)
    setPWM(M,'Pumps',system.sysItems['All'],0,0)
    
    to_turn_off = ['Stir','Thermostat','Heat','UV',
                   'Pump1','Pump2','Pump3','Pump4']
    for turn_off in to_turn_off:
        SetOutputOn(M,turn_off,0)


@application.route('/')
def index():
    #Function responsible for sending appropriate device's data to user interface. 
    global system
    
    outputdata=system.sysData[system.sysItems['UIDevice']]
    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            if system.sysData[M]['present']==1:
                outputdata['presentDevices'][M]=1
            else:
                outputdata['presentDevices'][M]=0
    return render_template('index.html',**outputdata)
    
@application.route('/getsysData/')
def getSysdata():
    #Similar to function above, packages data to be sent to UI.
    global system
    outputdata=system.sysData[system.sysItems['UIDevice']]
    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            if system.sysData[M]['present']==1:
                outputdata['presentDevices'][M]=1
            else:
                outputdata['presentDevices'][M]=0
    return jsonify(outputdata)

@application.route('/changeDevice/<M>',methods=['POST'])
def changeDevice(M):
    #Function responsible for changin which device is selected in the UI.
    global system
    M=str(M)
    if system.sysData[M]['present']==1:
        for Mb in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            system.sysData[Mb]['UIDevice']=M
        
        system.sysItems['UIDevice']=M

    return ('', 204)

@application.route('/scanDevices/<which>',methods=['POST'])
def scanDevices(which):
    #Scans to decide which devices are plugged in/on. Does this by trying to communicate with their internal thermometers (if this communication failes, software assumes device is not present)
    global system
    which=str(which)
    
    if which=="all":
        for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            system.sysData[M]['present']=1
            I2CCom(M,'ThermometerInternal',1,16,0x05,0,0) #We arbitrarily poll the thermometer to see if anything is plugged in! 
            system.sysData[M]['DeviceID']=GetID(M)
    else: 
        
        system.sysData[which]['present']=1
        I2CCom(which,'ThermometerInternal',1,16,0x05,0,0)
        system.sysData[which]['DeviceID']=GetID(which)

    return ('', 204)


def GetID(M):

    # Gets the CHi.Bio reactor's ID, which is basically just the unique ID of
    # the infrared thermometer.

    global system
    M=str(M)
    ID=''
    if system.sysData[M]['present']==1:
        pt1=str(I2CCom(M,'ThermometerIR',1,0,0x3C,0,1))
        pt2=str(I2CCom(M,'ThermometerIR',1,0,0x3D,0,1))
        pt3=str(I2CCom(M,'ThermometerIR',1,0,0x3E,0,1))
        pt4=str(I2CCom(M,'ThermometerIR',1,0,0x3F,0,1))
        ID = pt1+pt2+pt3+pt4
        
    return ID
    

def addTerminal(M,strIn):
    #Responsible for adding a new line to the terminal in the UI.
    global system
    now=datetime.now()
    timeString=now.strftime("%Y-%m-%d %H:%M:%S ")
    system.sysData[M]['Terminal']['text']=timeString + ' - ' +  str(strIn) + '</br>' + system.sysData[M]['Terminal']['text']
    
@application.route("/ClearTerminal/<M>",methods=['POST'])
def clearTerminal(M):
    #Deletes everything from the terminal.
    global system
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
        
    system.sysData[M]['Terminal']['text']=''
    addTerminal(M,'Terminal Cleared')
    return ('', 204)   
    


@application.route("/SetFPMeasurement/<item>/<Excite>/<Base>/<Emit1>/<Emit2>/<Gain>",methods=['POST'])
def SetFPMeasurement(item,Excite,Base,Emit1,Emit2,Gain):
    #Sets up the fluorescent protein measurement in terms of gain, and which LED / measurement bands to use.
    FP=str(item)
    Excite=str(Excite)
    Base=str(Base)
    Emit1=str(Emit1)
    Emit2=str(Emit2)
    Gain=str(Gain)
    M=system.sysItems['UIDevice']
    
    if system.sysData[M][FP]['ON']==1:
        system.sysData[M][FP]['ON']=0
        return ('', 204)
    else: 
        system.sysData[M][FP]['ON']=1
        system.sysData[M][FP]['LED']=Excite
        system.sysData[M][FP]['BaseBand']=Base
        system.sysData[M][FP]['Emit1Band']=Emit1
        system.sysData[M][FP]['Emit2Band']=Emit2
        system.sysData[M][FP]['Gain']=Gain
        return ('', 204)  
     

        
    
    

@application.route("/SetOutputTarget/<item>/<M>/<value>",methods=['POST'])
def SetOutputTarget(M,item, value):
    #General function used to set the output level of a particular item, ensuring it is within an acceptable range.
    global system
    item = str(item)
    value = float(value)
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
    print(str(datetime.now()) + " Set item: " + str(item) + " to value " + str(value) + " on " + str(M))
    if (value<system.sysData[M][item]['min']):
        value=system.sysData[M][item]['min']
    if (value>system.sysData[M][item]['max']):
        value=system.sysData[M][item]['max']
        
    system.sysData[M][item]['target']=value
    
    if(system.sysData[M][item]['ON']==1 and not(item=='OD' or item=='Thermostat')): #Checking to see if our item is already running, in which case
        SetOutputOn(M,item,0) #we turn it off and on again to restart at new rate.
        SetOutputOn(M,item,1)
    return ('', 204)    
    


    
@application.route("/SetOutputOn/<item>/<force>/<M>",methods=['POST'])
def SetOutputOn(M,item,force):
    #General function used to switch an output on or off.
    global system
    item = str(item)
    
    force = int(force)
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
    #The first statements are to force it on or off it the command is called in force mode (force implies it sets it to a given state, regardless of what it is currently in)
    if (force==1):
        system.sysData[M][item]['ON']=1
        SetOutput(M,item)
        return ('', 204)    
    
    elif(force==0):
        system.sysData[M][item]['ON']=0
        SetOutput(M,item)
        return ('', 204)    
    
    #Elsewise this is doing a flip operation (i.e. changes to opposite state to that which it is currently in)
    if (system.sysData[M][item]['ON']==0):
        system.sysData[M][item]['ON']=1
        SetOutput(M,item)
        return ('', 204)    
    
    else:
        system.sysData[M][item]['ON']=0
        SetOutput(M,item)
        return ('', 204)    


def SetOutput(M,item):
    #Here we actually do the digital communications required to set a given output. This function is called by SetOutputOn above as required.
    global system
    M=str(M)
    #We go through each different item and set it going as appropriate.
    if(item=='Stir'): 
        #Stirring is initiated at a high speed for a couple of seconds to prevent the stir motor from stalling (e.g. if it is started at an initial power of 0.3)
        if (system.sysData[M][item]['target']*float(system.sysData[M][item]['ON'])>0):
            setPWM(M,'PWM',system.sysItems[item],1.0*float(system.sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
            time.sleep(1.5)

            if (system.sysData[M][item]['target']>0.4 and system.sysData[M][item]['ON']==1):
                setPWM(M,'PWM',system.sysItems[item],0.5*float(system.sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
                time.sleep(0.75)
            
            if (system.sysData[M][item]['target']>0.8 and system.sysData[M][item]['ON']==1):
                setPWM(M,'PWM',system.sysItems[item],0.7*float(system.sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
                time.sleep(0.75)

        setPWM(M,'PWM',system.sysItems[item],system.sysData[M][item]['target']*float(system.sysData[M][item]['ON']),0)
        
        
    elif(item=='Heat'):
        setPWM(M,'PWM',system.sysItems[item],system.sysData[M][item]['target']*float(system.sysData[M][item]['ON']),0)
    elif(item=='UV'):
        setPWM(M,'PWM',system.sysItems[item],system.sysData[M][item]['target']*float(system.sysData[M][item]['ON']),0)
    elif (item=='Thermostat'):
        system.sysDevices[M][item]['thread']=Thread(target = Thermostat, args=(M,item))
        system.sysDevices[M][item]['thread'].setDaemon(True)
        system.sysDevices[M][item]['thread'].start()
        
    elif (item=='Pump1' or item=='Pump2' or item=='Pump3' or item=='Pump4'): 
        if (system.sysData[M][item]['target']==0):
            system.sysData[M][item]['ON']=0
        system.sysDevices[M][item]['thread']=Thread(target = PumpModulation, args=(M,item))
        
        system.sysDevices[M][item]['thread'].setDaemon(True)
        system.sysDevices[M][item]['thread'].start()

    elif (item=='OD'):
        SetOutputOn(M,'Pump1',0)
        SetOutputOn(M,'Pump2',0) #We turn pumps off when we switch OD state
    elif (item=='Zigzag'):
        system.sysData[M]['Zigzag']['target']=5.0
        system.sysData[M]['Zigzag']['SwitchPoint']=system.sysData[M]['Experiment']['cycles']
    
    elif (item=='LEDA' or item=='LEDB' or item=='LEDC' or item=='LEDD' or item=='LEDE' or item=='LEDF' or item=='LEDG'):
        setPWM(M,'PWM',system.sysItems[item],system.sysData[M][item]['target']*float(system.sysData[M][item]['ON']),0)
        
    else: #This is if we are setting the DAC. All should be in range [0,1]
        register = int(system.sysItems['DAC'][item],2)
        
        value=system.sysData[M][item]['target']*float(system.sysData[M][item]['ON']) 
        if (value==0):
            value=0
        else:
            value=(value+0.00)/1.00
            sf=0.303 #This factor is scaling down the maximum voltage being fed to the laser, preventing its photodiode current (and hence optical power) being too large.
            value=value*sf
        binaryValue=bin(int(value*4095.9)) #Bit of a dodgy method for ensuring we get an integer in [0,4095]
        toWrite=str(binaryValue[2:].zfill(16))
        toWrite1=int(toWrite[0:8],2)
        toWrite2=int(toWrite[8:16],2)
        I2CCom(M,'DAC',0,8,toWrite1,toWrite2,0)
       
        
        
    
    
        
  
def PumpModulation(M,item):
    #Responsible for turning pumps on/off with an appropriate duty cycle. They are turned on for a fraction of each ~1minute cycle to achieve low pump rates.
    global system
    
    system.sysDevices[M][item]['threadCount']=(system.sysDevices[M][item]['threadCount']+1)%100 #Index of the particular thread running.
    currentThread=system.sysDevices[M][item]['threadCount']
    
    while (system.sysDevices[M][item]['active']==1): #Idea is we will wait here if a previous thread on this pump is already running. Potentially all this 'active' business could be removed from this fuction.
        time.sleep(0.02)
        
    if (abs(system.sysData[M][item]['target']*system.sysData[M][item]['ON'])!=1 and currentThread==system.sysDevices[M][item]['threadCount']): #In all cases we turn things off to begin
        system.sysDevices[M][item]['active']=1
        setPWM(M,'Pumps',system.sysItems[item]['In1'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In1'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],0.0*float(system.sysData[M][item]['ON']),0)
        system.sysDevices[M][item]['active']=0
    if (system.sysData[M][item]['ON']==0):
        return
    
    Time1=datetime.now()
    cycletime=system.sysData[M]['Experiment']['cycleTime']*1.05 #We make this marginally longer than the experiment cycle time to avoid too much chaos when you come back around to pumping again.
    
    Ontime=cycletime*abs(system.sysData[M][item]['target'])
    
    # Decided to remove the below section in order to prevent media buildup in the device if you are pumping in very rapidly. This check means that media is removed, then added. Removing this code means these happen simultaneously.
    #if (item=="Pump1" and abs(system.sysData[M][item]['target'])<0.3): #Ensuring we run Pump1 after Pump2.
    #    waittime=cycletime*abs(system.sysData[M]['Pump2']['target']) #We want to wait until the output pump has stopped, otherwise you are very inefficient with your media since it will be pumping out the fresh media fromthe top of the test tube right when it enters.
    #    time.sleep(waittime+1.0)  
        
    
    if (system.sysData[M][item]['target']>0 and currentThread==system.sysDevices[M][item]['threadCount']): #Turning on pumps in forward direction
        system.sysDevices[M][item]['active']=1
        setPWM(M,'Pumps',system.sysItems[item]['In1'],1.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],0.0*float(system.sysData[M][item]['ON']),0)
        system.sysDevices[M][item]['active']=0
    elif (system.sysData[M][item]['target']<0 and currentThread==system.sysDevices[M][item]['threadCount']): #Or backward direction.
        system.sysDevices[M][item]['active']=1
        setPWM(M,'Pumps',system.sysItems[item]['In1'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],1.0*float(system.sysData[M][item]['ON']),0)
        system.sysDevices[M][item]['active']=0
  
    time.sleep(Ontime)
    
    if(abs(system.sysData[M][item]['target'])!=1 and currentThread==system.sysDevices[M][item]['threadCount']): #Turning off pumps at appropriate time.
        system.sysDevices[M][item]['active']=1
        setPWM(M,'Pumps',system.sysItems[item]['In1'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In1'],0.0*float(system.sysData[M][item]['ON']),0)
        setPWM(M,'Pumps',system.sysItems[item]['In2'],0.0*float(system.sysData[M][item]['ON']),0)
        system.sysDevices[M][item]['active']=0
    
    Time2=datetime.now()
    elapsedTime=Time2-Time1
    elapsedTimeSeconds=round(elapsedTime.total_seconds(),2)
    Offtime=cycletime-elapsedTimeSeconds
    if (Offtime>0.0):
        time.sleep(Offtime)   
    
    
    if (system.sysData[M][item]['ON']==1 and system.sysDevices[M][item]['threadCount']==currentThread): #If pumps need to keep going, this starts a new pump thread.
        system.sysDevices[M][item]['thread']=Thread(target = PumpModulation, args=(M,item))
        system.sysDevices[M][item]['thread'].setDaemon(True)
        system.sysDevices[M][item]['thread'].start()
    
        


def Thermostat(M,item):
    #Function that implements thermostat temperature control using MPC algorithm.
    global system

    ON=system.sysData[M][item]['ON']
    system.sysDevices[M][item]['threadCount']=(system.sysDevices[M][item]['threadCount']+1)%100
    currentThread=system.sysDevices[M][item]['threadCount']
    
    if (ON==0):
        SetOutputOn(M,'Heat',0)
        return
    
    MeasureTemp(M,'IR') #Measures temperature - note that this may be happening DURING stirring.

    CurrentTemp=system.sysData[M]['ThermometerIR']['current']
    TargetTemp=system.sysData[M]['Thermostat']['target']
    LastTemp=system.sysData[M]['Thermostat']['last']
    
    #MPC Controller Component
    MediaTemp=system.sysData[M]['ThermometerExternal']['current']
    MPC=0
    if (MediaTemp>0.0):
        Tdiff=CurrentTemp-MediaTemp
        Pumping=system.sysData[M]['Pump1']['target']*float(system.sysData[M]['Pump1']['ON'])*float(system.sysData[M]['OD']['ON'])
        Gain=2.5
        MPC=Gain*Tdiff*Pumping
        
        
    #PI Controller Component
    e=TargetTemp-CurrentTemp
    dt=system.sysData[M]['Thermostat']['cycleTime']
    I=system.sysData[M]['Thermostat']['Integral']
    if (abs(e)<2.0):
        I=I+0.0005*dt*e
        P=0.25*e
    else:
        P=0.5*e
    
    if (abs(TargetTemp-LastTemp)>2.0): #This resets integrator if we make a big jump in set point.
        I=0.0
    elif(I<0.0):
        I=0.0
    elif (I>1.0):
        I=1.0
    
    system.sysData[M]['Thermostat']['Integral']=I

    U=P+I+MPC
    
    if(U>1.0):
        U=1.0
        system.sysData[M]['Heat']['target']=U
        system.sysData[M]['Heat']['ON']=1
    elif(U<0):  
        U=0
        system.sysData[M]['Heat']['target']=U
        system.sysData[M]['Heat']['ON']=0
    else:
        system.sysData[M]['Heat']['target']=U
        system.sysData[M]['Heat']['ON']=1
    
    system.sysData[M]['Thermostat']['last']=system.sysData[M]['Thermostat']['target']
   
    SetOutput(M,'Heat')
    
    time.sleep(dt)  
        
    
    if (system.sysData[M][item]['ON']==1 and system.sysDevices[M][item]['threadCount']==currentThread):
        system.sysDevices[M][item]['thread']=Thread(target = Thermostat, args=(M,item))
        system.sysDevices[M][item]['thread'].setDaemon(True)
        system.sysDevices[M][item]['thread'].start()
    else:
        system.sysData[M]['Heat']['ON']=0
        system.sysData[M]['Heat']['target']=0
        SetOutput(M,'Heat')
        
        
    
    

@application.route("/Direction/<item>/<M>",methods=['POST'])
def direction(M,item):
    #Flips direction of a pump.
    global system
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
    system.sysData[M][item]['target']=-1.0*system.sysData[M][item]['target']
    if (system.sysData[M]['OD']['ON']==1):
            system.sysData[M][item]['direction']=-1.0*system.sysData[M][item]['direction']

    return ('', 204)  
    

    
def AS7341Read(M,Gain,ISteps,reset):
    #Responsible for reading data from the spectrometer.
    global system
    reset=int(reset)
    ISteps=int(ISteps)
    if ISteps>255:
        ISteps=255 #255 steps is approx 0.71 seconds.
    elif (ISteps<0):
        ISteps=0
    if Gain>10:
        Gain=10 #512x
    elif (Gain<0):
        Gain=0 #0.5x

    I2CCom(M,'AS7341',0,8,int(0xA9),int(0x04),0) #This sets us into BANK mode 0, for accesing registers 0x80+. The 4 means we have WTIMEx16
    if (reset==1):
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x00),0) #Turns power down
        time.sleep(0.01)
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0) #Turns power on with spectral measurement disabled
    else:
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0)  #Turns power on with spectral measurement disabled

    I2CCom(M,'AS7341',0,8,int(0xAF),int(0x10),0) #Tells it we are going to now write SMUX configuration to RAM
    
    
    #I2CCom(M,'AS7341',0,100,int(0x00),int(0x00),0) #Forces AS7341SMUX to run since length is 100.
    AS7341SMUX(M,'AS7341',0,0)
    
    I2CCom(M,'AS7341',0,8,int(0x80),int(0x11),0)  #Runs SMUX command (i.e. cofigures SMUX with data from ram)
    time.sleep(0.001)
    I2CCom(M,'AS7341',0,8,int(0x81),ISteps,0)  #Sets number of integration steps of length 2.78ms Max ISteps is 255
    I2CCom(M,'AS7341',0,8,int(0x83),0xFF,0)  #Sets maxinum wait time of 0.7mS (multiplex by 16 due to WLONG)
    I2CCom(M,'AS7341',0,8,int(0xAA),Gain,0)  #Sets gain on ADCs. Maximum value of Gain is 10 and can take values from 0 to 10.
    #I2CCom(M,'AS7341',0,8,int(0xA9),int(0x14),0) #This sets us into BANK mode 1, for accessing 0x60 to 0x74. The 4 means we have WTIMEx16
    #I2CCom(M,'AS7341',0,8,int(0x70),int(0x00),0)  #Sets integration mode SPM (normal mode)
    #Above is default of 0x70!
    I2CCom(M,'AS7341',0,8,int(0x80),int(0x0B),0)  #Starts spectral measurement, with WEN (wait between measurements feature) enabled.
    time.sleep((ISteps+1)*0.0028 + 0.2) #Wait whilst integration is done and results are processed. 
    
    ASTATUS=int(I2CCom(M,'AS7341',1,8,0x94,0x00,0)) #Get measurement status, including saturation details.
    C0_L=int(I2CCom(M,'AS7341',1,8,0x95,0x00,0))
    C0_H=int(I2CCom(M,'AS7341',1,8,0x96,0x00,0))
    C1_L=int(I2CCom(M,'AS7341',1,8,0x97,0x00,0))
    C1_H=int(I2CCom(M,'AS7341',1,8,0x98,0x00,0))
    C2_L=int(I2CCom(M,'AS7341',1,8,0x99,0x00,0))
    C2_H=int(I2CCom(M,'AS7341',1,8,0x9A,0x00,0))
    C3_L=int(I2CCom(M,'AS7341',1,8,0x9B,0x00,0))
    C3_H=int(I2CCom(M,'AS7341',1,8,0x9C,0x00,0))
    C4_L=int(I2CCom(M,'AS7341',1,8,0x9D,0x00,0))
    C4_H=int(I2CCom(M,'AS7341',1,8,0x9E,0x00,0))
    C5_L=int(I2CCom(M,'AS7341',1,8,0x9F,0x00,0))
    C5_H=int(I2CCom(M,'AS7341',1,8,0xA0,0x00,0))

    I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0)  #Stops spectral measurement, leaves power on.

    #Status2=int(I2CCom(M,'AS7341',1,8,0xA3,0x00,0)) #Reads system status at end of spectral measursement. 
    #print(str(ASTATUS))
    #print(str(Status2))

    system.sysData[M]['AS7341']['current']['ADC0']=int(bin(C0_H)[2:].zfill(8)+bin(C0_L)[2:].zfill(8),2)
    system.sysData[M]['AS7341']['current']['ADC1']=int(bin(C1_H)[2:].zfill(8)+bin(C1_L)[2:].zfill(8),2)
    system.sysData[M]['AS7341']['current']['ADC2']=int(bin(C2_H)[2:].zfill(8)+bin(C2_L)[2:].zfill(8),2)
    system.sysData[M]['AS7341']['current']['ADC3']=int(bin(C3_H)[2:].zfill(8)+bin(C3_L)[2:].zfill(8),2)
    system.sysData[M]['AS7341']['current']['ADC4']=int(bin(C4_H)[2:].zfill(8)+bin(C4_L)[2:].zfill(8),2)
    system.sysData[M]['AS7341']['current']['ADC5']=int(bin(C5_H)[2:].zfill(8)+bin(C5_L)[2:].zfill(8),2)
    
    
    if (system.sysData[M]['AS7341']['current']['ADC0']==65535 or system.sysData[M]['AS7341']['current']['ADC1']==65535 or system.sysData[M]['AS7341']['current']['ADC2']==65535 or system.sysData[M]['AS7341']['current']['ADC3']==65535 or system.sysData[M]['AS7341']['current']['ADC4']==65535 or system.sysData[M]['AS7341']['current']['ADC5']==65535 ):
        print(str(datetime.now()) + ' Spectrometer measurement was saturated on device ' + str(M)) #Not sure if this saturation check above actually works correctly...
    return 0
        

def AS7341SMUX(M,device,data1,data2):
    #Sets up the ADC multiplexer on the spectrometer, this is responsible for connecting photodiodes to amplifier/adc circuits within the device. 
    #The spectrometer has only got 6 ADCs but >6 photodiodes channels, hence you need to select a subset of photodiodes to measure with each shot. The relative gain does change slightly (1-2%) between ADCs.
    global system
    M=str(M)
    Addresses=['0x00','0x01','0x02','0x03','0x04','0x05','0x06','0x07','0x08','0x0A','0x0B','0x0C','0x0D','0x0E','0x0F','0x10','0x11','0x12']
    for a in Addresses:
        A=system.sysItems['AS7341'][a]['A']
        B=system.sysItems['AS7341'][a]['B']
        if (A!='U'):
            As=system.sysData[M]['AS7341']['channels'][A]
        else:
            As=0
        if (B!='U'):
            Bs=system.sysData[M]['AS7341']['channels'][B]
        else:
            Bs=0
        Ab=str(bin(As))[2:].zfill(4)
        Bb=str(bin(Bs))[2:].zfill(4)
        C=Ab+Bb
        #time.sleep(0.001) #Added this to remove errors where beaglebone crashed!
        I2CCom(M,'AS7341',0,8,int(a,16),int(C,2),0) #Tells it we are going to now write SMUX configuration to RAM
        #system.sysDevices[M][device]['device'].write8(int(a,16),int(C,2))


@application.route("/GetSpectrum/<Gain>/<M>",methods=['POST'])
def GetSpectrum(M,Gain):
    #Measures entire spectrum, i.e. every different photodiode, which requires 2 measurement shots. 
    Gain=int(Gain[1:])
    global system
    M=str(M)   
    if (M=="0"):
        M=system.sysItems['UIDevice']
    out=GetLight(M,['nm410','nm440','nm470','nm510','nm550','nm583'],Gain,255)
    out2=GetLight(M,['nm620', 'nm670','CLEAR','NIR','DARK'],Gain,255)
    system.sysData[M]['AS7341']['spectrum']['nm410']=out[0]
    system.sysData[M]['AS7341']['spectrum']['nm440']=out[1]
    system.sysData[M]['AS7341']['spectrum']['nm470']=out[2]
    system.sysData[M]['AS7341']['spectrum']['nm510']=out[3]
    system.sysData[M]['AS7341']['spectrum']['nm550']=out[4]
    system.sysData[M]['AS7341']['spectrum']['nm583']=out[5]
    system.sysData[M]['AS7341']['spectrum']['nm620']=out2[0]
    system.sysData[M]['AS7341']['spectrum']['nm670']=out2[1]
    system.sysData[M]['AS7341']['spectrum']['CLEAR']=out2[2]
    system.sysData[M]['AS7341']['spectrum']['NIR']=out2[3]
    
        
    return ('', 204)   
    


    
def GetLight(M,wavelengths,Gain,ISteps):
    #Runs spectrometer measurement and puts data into appropriate structure.
    global system
    M=str(M)
    channels=['nm410','nm440','nm470','nm510','nm550','nm583','nm620', 'nm670','CLEAR','NIR','DARK','ExtGPIO', 'ExtINT' , 'FLICKER']
    for channel in channels:
        system.sysData[M]['AS7341']['channels'][channel]=0 #First we set all measurement ADC indexes to zero.
    index=1
    for wavelength in wavelengths:
        if wavelength != "OFF":
            system.sysData[M]['AS7341']['channels'][wavelength]=index #Now assign ADCs to each of the channel where needed. 
        index=index+1

    success=0
    while success<2:
        try:
            AS7341Read(M,Gain,ISteps,success) 
            success=2
        except:
            print(str(datetime.now()) + 'AS7341 measurement failed on ' + str(M))
            success=success+1
            if success==2:
                print(str(datetime.now()) + 'AS7341 measurement failed twice on ' + str(M) + ', setting unity values')
                system.sysData[M]['AS7341']['current']['ADC0']=1
                DACS=['ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
                for DAC in DACS:
                    system.sysData[M]['AS7341']['current'][DAC]=0

    output=[0.0,0.0,0.0,0.0,0.0,0.0]
    index=0
    DACS=['ADC0', 'ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
    for wavelength in wavelengths:
        if wavelength != "OFF":
            output[index]=system.sysData[M]['AS7341']['current'][DACS[index]]
        index=index+1

    return output


def GetTransmission(M,item,wavelengths,Gain,ISteps):
    #Gets light transmission through sample by turning on light, measuring, turning off light.
    global system
    M=str(M)
    SetOutputOn(M,item,1)
    output=GetLight(M,wavelengths,Gain,ISteps)
    SetOutputOn(M,item,0)
    return output


@application.route("/SetCustom/<Program>/<Status>",methods=['POST'])
def SetCustom(Program,Status):
    #Turns a custom program on/off.
	
    global system
    M=system.sysItems['UIDevice']
    item="Custom"
    if system.sysData[M][item]['ON']==1:
        system.sysData[M][item]['ON']=0
    else:
        system.sysData[M][item]['Program']=str(Program)
        system.sysData[M][item]['Status']=float(Status)
        system.sysData[M][item]['ON']=1
        system.sysData[M][item]['param1']=0.0 #Thus parameters get reset each time you restart your program.
        system.sysData[M][item]['param2']=0.0
        system.sysData[M][item]['param3']=0.0
    return('',204)
		
        
def CustomProgram(M):
    #Runs a custom program, some examples are included. You can remove/edit this function as you see fit.
    #Note that the custom programs (as set up at present) use an external .csv file with input parameters. THis is done to allow these parameters to easily be varied on the fly. 
    global system
    M=str(M)
    program=system.sysData[M]['Custom']['Program']
    #Subsequent few lines reads in external parameters from a file if you are using any.
    fname='InputParameters_' + str(M)+'.csv'
	
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        listin = list(reader)
    Params=listin[0]
    addTerminal(M,'Running Program = ' + str(program) + ' on device ' + str(M))
	
	
    if (program=="C1"): #Optogenetic Integral Control Program
        integral=0.0 #Integral in integral controller
        green=0.0 #Intensity of Green actuation 
        red=0.0 #Intensity of red actuation.
        GFPNow=system.sysData[M]['FP1']['Emit1']
        GFPTarget=system.sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GFPTarget-GFPNow
        if error>0.0075:
            green=1.0
            red=0.0
            system.sysData[M]['Custom']['param3']=0.0 
        elif error<-0.0075:
            green=0.0
            red=1.0
            system.sysData[M]['Custom']['param3']=0.0
        else:
            red=1.0
            balance=float(Params[0]) #our guess at green light level to get 50% expression.
            KI=float(Params[1])
            KP=float(Params[2])
            integral=system.sysData[M]['Custom']['param3']+error*KI
            green=balance+KP*error+integral
            system.sysData[M]['Custom']['param3']=integral
        

        GreenThread=Thread(target = CustomLEDCycle, args=(M,'LEDD',green))
        GreenThread.setDaemon(True)
        GreenThread.start()
        RedThread=Thread(target = CustomLEDCycle, args=(M,'LEDF',red))
        RedThread.setDaemon(True)
        RedThread.start()
        system.sysData[M]['Custom']['param1']=green
        system.sysData[M]['Custom']['param2']=red
        addTerminal(M,'Program = ' + str(program) + ' green= ' + str(green)+ ' red= ' + str(red) + ' integral= ' + str(integral))
	
    elif (program=="C2"): #UV Integral Control Program
        integral=0.0 #Integral in integral controller
        UV=0.0 #Intensity of Green actuation 
        GrowthRate=system.sysData[M]['GrowthRate']['current']
        GrowthTarget=system.sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GrowthTarget-GrowthRate
        KP=float(Params[0]) #Past data suggest value of ~0.005
        KI=float(Params[1]) #Past data suggest value of ~2e-5
        integral=system.sysData[M]['Custom']['param2']+error*KI
        if(integral>0):
            integral=0.0
        system.sysData[M]['Custom']['param2']=integral
        UV=-1.0*(KP*error+integral)
        system.sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        addTerminal(M,'Program = ' + str(program) + ' UV= ' + str(UV)+  ' integral= ' + str(integral))
        
    elif (program=="C3"): #UV Integral Control Program Mk 2
        integral=system.sysData[M]['Custom']['param2'] #Integral in integral controller
        integral2=system.sysData[M]['Custom']['param3'] #Second integral controller
        UV=0.0 #Intensity of UV
        GrowthRate=system.sysData[M]['GrowthRate']['current']
        GrowthTarget=system.sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GrowthTarget-GrowthRate
        KP=float(Params[0]) #Past data suggest value of ~0.005
        KI=float(Params[1]) #Past data suggest value of ~2e-5
        KI2=float(Params[2])
        integral=system.sysData[M]['Custom']['param2']+error*KI
        if(integral>0):
            integral=0.0
            
        if(abs(error)<0.3): #This is a second high-gain integrator which only gets cranking along when we are close to the target.
            integral2=system.sysData[M]['Custom']['param3']+error*KI2
        if(integral2>0):
            integral2=0.0
            
        system.sysData[M]['Custom']['param2']=integral
        system.sysData[M]['Custom']['param3']=integral2
        UV=-1.0*(KP*error+integral+integral2)
        m=50.0
        UV=(1.0/m)*(math.exp(m*UV)-1.0) #Basically this is to force the UV level to increase exponentially!
        system.sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        addTerminal(M,'Program = ' + str(program) + ' UV= ' + str(UV)+  ' integral= ' + str(integral))
    elif (program=="C4"): #UV Integral Control Program Mk 4
        rategain=float(Params[0]) 
        timept=system.sysData[M]['Custom']['Status'] #This is the timestep as we follow in minutes
        
        UV=0.001*math.exp(timept*rategain) #So we just exponentialy increase UV over time!
        system.sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        
        timept=timept+1
        system.sysData[M]['Custom']['Status']=timept
            
    elif (program=="C5"): #UV Dosing program
        timept=int(system.sysData[M]['Custom']['Status']) #This is the timestep as we follow in minutes
        system.sysData[M]['Custom']['Status']=timept+1 #Increment time as we have entered the loop another time!
        
        Pump2Ontime=system.sysData[M]['Experiment']['cycleTime']*1.05*abs(system.sysData[M]['Pump2']['target'])*system.sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
        time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
        
        timelength=300 #Time between doses in minutes
        if(timept%timelength==2): #So this happens every 5 hours!
            iters=(timept//timelength)
            Dose0=float(Params[0])
            Dose=Dose0*(2.0**float(iters)) #UV Dose, in terms of amount of time UV shoudl be left on at 1.0 intensity.
            print(str(datetime.now()) + ' Gave dose ' + str(Dose) + " at iteration " + str(iters) + " on device " + str(M))
            
            if (Dose<30.0):  
                powerlvl=Dose/30.0
                SetOutputTarget(M,'UV',powerlvl)
                Dose=30.0
            else:    
                SetOutputTarget(M,'UV',1.0) #Ensure UV is on at aopropriate intensity
                
            SetOutputOn(M,'UV',1) #Activate UV
            time.sleep(Dose) #Wait for dose to be administered
            SetOutputOn(M,'UV',0) #Deactivate UV
            
    elif (program=="C6"): #UV Dosing program 2 - constant value!
        timept=int(system.sysData[M]['Custom']['Status']) #This is the timestep as we follow in minutes
        system.sysData[M]['Custom']['Status']=timept+1 #Increment time as we have entered the loop another time!
        
        Pump2Ontime=system.sysData[M]['Experiment']['cycleTime']*1.05*abs(system.sysData[M]['Pump2']['target'])*system.sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
        time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
    
        timelength=300 #Time between doses in minutes
        if(timept%timelength==2): #So this happens every 5 hours!
            iters=(timept//timelength)
            if iters>3:
                iters=3
                
            Dose0=float(Params[0])
            Dose=Dose0*(2.0**float(iters)) #UV Dose, in terms of amount of time UV shoudl be left on at 1.0 intensity.
            print(str(datetime.now()) + ' Gave dose ' + str(Dose) + " at iteration " + str(iters) + " on device " + str(M))
              
            if (Dose<30.0):  
                powerlvl=Dose/30.0
                SetOutputTarget(M,'UV',powerlvl)
                Dose=30.0
            else:    
                SetOutputTarget(M,'UV',1.0) #Ensure UV is on at aopropriate intensity
            
            SetOutputOn(M,'UV',1) #Activate UV
            time.sleep(Dose) #Wait for dose to be administered
            SetOutputOn(M,'UV',0) #Deactivate UV
                
                
    
    return

def CustomLEDCycle(M,LED,Value):
    #This function cycles LEDs for a fraction of 30 seconds during an experiment.
    global system
    M=str(M)
    if (Value>1.0):
        Value=1.0
        
    if (Value>0.0):
        SetOutputOn(M,LED,1)
        time.sleep(Value*30.0)#Sleep whatever fraction of 30 seconds we are interested in
        SetOutputOn(M,LED,0)
        
    return


@application.route("/SetLightActuation/<Excite>",methods=['POST'])
def SetLightActuation(Excite):
    #Basic function used to set which LED is used for optogenetics.
    global system
    M=system.sysItems['UIDevice']
    item="Light"
    if system.sysData[M][item]['ON']==1:
        system.sysData[M][item]['ON']=0
        return ('', 204)
    else:
        system.sysData[M][item]['Excite']=str(Excite)
        system.sysData[M][item]['ON']=1
        return('',204)
        
        
        
def LightActuation(M,toggle):
    #Another optogenetic function, turning LEDs on/off during experiment as appropriate.
    global system
    M=str(M)
    toggle=int(toggle)
    LEDChoice=system.sysData[M]['Light']['Excite']
    if (toggle==1 and system.sysData[M]['Light']['ON']==1):
        SetOutputOn(M,LEDChoice,1)
    else:
        SetOutputOn(M,LEDChoice,0)
    return 0


@application.route("/CharacteriseDevice/<M>/<Program>",methods=['POST'])     
def CharacteriseDevice(M,Program): 
    # THis umbrella function is used to run the actual characteriseation function in a thread to prevent GUnicorn worker timeout.
    Program=str(Program)
    if (Program=='C1'):
        cthread=Thread(target = CharacteriseDevice2, args=(M))
        cthread.setDaemon(True)
        cthread.start()
    
    return('',204)
        
        
        
def CharacteriseDevice2(M):
    global system
    print('In1')
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
        
    result= { 'LEDA' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDB' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDC' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDD' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDE' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDF' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDG' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LASER650' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        }
        
        
    print('Got in!')   
    bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR']    
    powerlevels=[0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
    items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    gains=['x4','x4','x4','x4','x4','x4','x4','x1']
    gi=-1
    for item in items:
        gi=gi+1
        for power in powerlevels:
            SetOutputTarget(M,item,power)
            SetOutputOn(M,item,1)
            GetSpectrum(M,gains[gi])
            SetOutputOn(M,item,0)
            print(item + ' ' + str(power))
            for band in bands:
                result[item][band].append(int(system.sysData[M]['AS7341']['spectrum'][band]))
            addTerminal(M,'Measured Item = ' + str(item) + ' at power ' + str(power))
            time.sleep(0.05)
                
    
    filename = 'characterisation_data_' + M + '.txt'
    f = open(filename,'w')
    simplejson.dump(result,f)
    f.close()
    return
  

def print_msg(msg):
    """
    Print a message to stdout.
    
    Parameters
    ----------
    msg : str
        message string
    """
    t = str(datetime.now())
    print(f"{t} {msg}",flush=True)

def shutdown(system):
    """
    Shutdown the system.
    
    Parameters
    ----------
    system : SystemConfiguration
        SystemConfiguration instance controlling device
    """
    print("Shutting down.",flush=True)

    # Basically this will crash all the electronics and the software. 
    system.sysItems['Watchdog']['ON'] = 0 


def I2CCom(M,device,rw,hl,data1,data2,SMBUSFLAG):
    """
    Function used to manage I2C bus communications for ALL devices.

    Parameters
    ----------
    M : str
        turbidistat name
    device : str
        name of device on turbidistat (pumps, etc.)
    rw : int
        read/write flag. 1 if read, 0 if write
    hl : int
        data size, 8 or 16
    data1 : int
        first data register
    data2 : int
        second data register. 
    SMBUSFLAG : int
        if set to 1, we are communicating with an SMBUs device

    Returns
    -------
    out : int
        output read from device or 0 (if no output)
    """

    M = str(M)           
    device = str(device) 
    rw = int(rw)         
    hl = int(hl)        
    SMBUSFLAG = int(SMBUSFLAG) 
    data1 = int(data1) 
    if hl < 20:
        data2 = int(data2) 

    global system

    keep_trying = True

    # Something stupid has happened in software if this is the case!
    if system.sysData[M]['present'] == 0: 
        print_msg("Trying to communicate with absent device - bug in software! Disabling hardware and software!")
        shutdown(system)
        keep_trying = False

    # Any time a thread gets to this point it will wait until the lock is free. Then
    # only one thread at a time will advance. 
    lock.acquire()

    # We now connect the multiplexer to the appropriate device to allow digital communications.
    tries = 0
    while keep_trying: 
        try:

            # We have established connection to correct device.
            system.sysItems['Multiplexer']['device'].write8(int(0x00),int(system.sysItems['Multiplexer'][M],2))

            # We check that the Multiplexer is indeed connected to the correct channel.  
            check = system.sysItems['Multiplexer']['device'].readRaw8()

            if check == int(system.sysItems['Multiplexer'][M],2):
                keep_trying = False
            else:
                tries = tries + 1
                time.sleep(0.02)
                print_msg(f"Multiplexer didn't switch {tries} times on {M}")
        
        # If there is an error in the above.
        except Exception as e: 
            tries = tries + 1
            time.sleep(0.02)
            print_msg(f"Failed multiplexer comms {tries} times")

            if tries > 2:
                
                try:
                    # Disconnect multiplexer.
                    system.sysItems['Multiplexer']['device'].write8(int(0x00),int(0x00))
                    print_msg(f"Disconnected multiplexer on {M}, trying to connect again.")  
                except:
                    print_msg(f"Failed to recover multiplexer on device {M}.")

            if tries == 5 or tries == 10 or tries == 15:
                
                # Flip the watchdog pin to ensure it is working.
                toggleWatchdog()  

                # Flip the Multiplexer RESET pin. Note this reset function works on Control Board V1.2 and later.
                GPIO.output('P8_15', GPIO.LOW) 
                time.sleep(0.1)
                GPIO.output('P8_15', GPIO.HIGH)
                time.sleep(0.1)
                print_msg(f"Did multiplexer hard-reset on {M}")
                
        # If it has failed a number of times then likely something is seriously wrong, so we crash the software.
        if tries > 20:
            print_msg("Failed to communicate with multiplexer 20 times. Disabling hardware and software!")
            shutdown(system)
            keep_trying = False
    
    time.sleep(0.0005)
    
    # We now do appropriate read/write on the bus.
    out = 0
    tries = 0
    keep_trying = True
    while keep_trying:
        try:
            if SMBUSFLAG == 0:
                if rw == 1:
                    if hl == 8:
                        out = int(system.sysDevices[M][device]['device'].readU8(data1))
                    elif hl == 16:
                        out = int(system.sysDevices[M][device]['device'].readU16(data1,data2))
                else:
                    if hl == 8:
                        system.sysDevices[M][device]['device'].write8(data1,data2)
                        out = 1
                    elif hl == 16:
                        system.sysDevices[M][device]['device'].write16(data1,data2)
                        out = 1
                    
            elif SMBUSFLAG == 1:
                out = system.sysDevices[M][device]['device'].read_word_data(system.sysDevices[M][device]['address'],data1)

            keep_trying = False

        # If the above fails then we can try again (a limited number of times)
        except Exception as e: 

            tries = tries + 1
            
            if device != "ThermometerInternal":
                print_msg(f"Failed {device} comms {tries} times on device {M}.")
                print_msg(f"Raised exception: {e.message}")
                time.sleep(0.02)
    
            if device == 'AS7341':
                print_msg(f"Failed AS7341 in I2CCom while trying to send {data1} and {data2}")
                print_msg(f"Raised exception: {e.message}")
                out = -1
                keep_trying = False


            # We don't allow the internal thermometer to fail, since this is what we
            # are using to see if devices are plugged in at all.
            if tries > 2 and device == "ThermometerInternal":
                print_msg(f"Internal thermometer failed. Fatal error.")
                system.sysData[M]['present'] = 0
                shutdown(system)
                keep_trying = False
                out = 0
        
            # In this case something else has gone wrong, so we panic.
            if tries > 10: 
                print_msg("Failed to communicate to a device 10 times. Disabling hardware and software!")
                system.sysData[M]['present'] = 0
                shutdown(system)
                keep_trying = False
                out = 0

    time.sleep(0.0005)
    
    try:
        # Disconnect multiplexer with each iteration. 
        system.sysItems['Multiplexer']['device'].write8(int(0x00),int(0x00)) 
    except:
        print_msg(f"Failed to disconnect a multiplexer on device {M}")
        
    # Bus lock is released so next command can occur.
    lock.release() 
    
    return out
    
    
@application.route("/CalibrateOD/<item>/<M>/<value>/<value2>",methods=['POST'])
def CalibrateOD(M,item,value,value2):
    #Used to calculate calibration value for OD measurements.
    global system
    item = str(item)
    ODRaw = float(value)
    ODActual = float(value2)
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
        
    device=system.sysData[M]['OD']['device']
    if (device=='LASER650'):
        a=system.sysData[M]['OD0']['LASERa']#Retrieve the calibration factors for OD.
        b=system.sysData[M]['OD0']['LASERb'] 
        if (ODActual<0):
            ODActual=0
            print(str(datetime.now()) + "You put a negative OD into calibration! Setting it to 0")
        
        raw=((ODActual/a +  (b/(2*a))**2)**0.5) - (b/(2*a)) #THis is performing the inverse function of the quadratic OD calibration.
        OD0=(10.0**raw)*ODRaw
        if (OD0<system.sysData[M][item]['min']):
            OD0=system.sysData[M][item]['min']
            print(str(datetime.now()) + 'OD calibration value seems too low?!')

        if (OD0>system.sysData[M][item]['max']):
            OD0=system.sysData[M][item]['max']
            print(str(datetime.now()) + 'OD calibration value seems too high?!')

    
        system.sysData[M][item]['target']=OD0
        print(str(datetime.now()) + "Calibrated OD")
    elif (device=='LEDF'):
        a=system.sysData[M]['OD0']['LEDFa']#Retrieve the calibration factors for OD.
        
        if (ODActual<0):
            ODActual=0
            print("You put a negative OD into calibration! Setting it to 0")
        if (M=='M0'):
            CF=1299.0
        elif (M=='M1'):
            CF=1206.0
        elif (M=='M2'):
            CF=1660.0
        elif (M=='M3'):
            CF=1494.0
            
        #raw=(ODActual)/a  #THis is performing the inverse function of the linear OD calibration.
        #OD0=ODRaw - raw*CF
        OD0=ODRaw/ODActual
        print(OD0)
    
        if (OD0<system.sysData[M][item]['min']):
            OD0=system.sysData[M][item]['min']
            print('OD calibration value seems too low?!')
        if (OD0>system.sysData[M][item]['max']):
            OD0=system.sysData[M][item]['max']
            print('OD calibration value seems too high?!')
    
        system.sysData[M][item]['target']=OD0
        print("Calibrated OD")
    elif (device=='LEDA'):
        a=system.sysData[M]['OD0']['LEDAa']#Retrieve the calibration factors for OD.
        
        if (ODActual<0):
            ODActual=0
            print("You put a negative OD into calibration! Setting it to 0")
        if (M=='M0'):
            CF=422
        elif (M=='M1'):
            CF=379
        elif (M=='M2'):
            CF=574
        elif (M=='M3'):
            CF=522
            
        #raw=(ODActual)/a  #THis is performing the inverse function of the linear OD calibration.
        #OD0=ODRaw - raw*CF
        OD0=ODRaw/ODActual
        print(OD0)
    
        if (OD0<system.sysData[M][item]['min']):
            OD0=system.sysData[M][item]['min']
            print('OD calibration value seems too low?!')
        if (OD0>system.sysData[M][item]['max']):
            OD0=system.sysData[M][item]['max']
            print('OD calibration value seems too high?!')
    
        system.sysData[M][item]['target']=OD0
        print("Calibrated OD")
        
    return ('', 204)    
    
    
        
@application.route("/MeasureOD/<M>",methods=['POST'])
def MeasureOD(M):
    #Measures laser transmission and calculates calibrated OD from this.
    global system

    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
    device=system.sysData[M]['OD']['device']
    if (device=='LASER650'):
        out=GetTransmission(M,'LASER650',['CLEAR'],1,255)
        system.sysData[M]['OD0']['raw']=float(out[0])
    
        a=system.sysData[M]['OD0']['LASERa']#Retrieve the calibration factors for OD.
        b=system.sysData[M]['OD0']['LASERb'] 
        try:
            raw=math.log10(system.sysData[M]['OD0']['target']/system.sysData[M]['OD0']['raw'])
            system.sysData[M]['OD']['current']=raw*b + raw*raw*a
        except:
            system.sysData[M]['OD']['current']=0
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))
    elif (device=='LEDF'):
        out=GetTransmission(M,'LEDF',['CLEAR'],7,255)

        system.sysData[M]['OD0']['raw']=out[0]
        a=system.sysData[M]['OD0']['LEDFa']#Retrieve the calibration factors for OD.
        try:
            if (M=='M0'):
                CF=1299.0
            elif (M=='M1'):
                CF=1206.0
            elif (M=='M2'):
                CF=1660.0
            elif (M=='M3'):
                CF=1494.0
            #raw=out[0]/CF - system.sysData[M]['OD0']['target']/CF
            raw=out[0]/system.sysData[M]['OD0']['target']
            system.sysData[M]['OD']['current']=raw
        except:
            system.sysData[M]['OD']['current']=0
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))

    elif (device=='LEDA'):
        out=GetTransmission(M,'LEDA',['CLEAR'],7,255)

        system.sysData[M]['OD0']['raw']=out[0]
        a=system.sysData[M]['OD0']['LEDAa']#Retrieve the calibration factors for OD.
        try:
            if (M=='M0'):
                CF=422.0
            elif (M=='M1'):
                CF=379.0
            elif (M=='M2'):
                CF=574.0
            elif (M=='M3'):
                CF=522.0
            #raw=out[0]/CF - system.sysData[M]['OD0']['target']/CF
            raw=out[0]/system.sysData[M]['OD0']['target']
            #system.sysData[M]['OD']['current']=raw*a
            system.sysData[M]['OD']['current']=raw
        except:
            system.sysData[M]['OD']['current']=0
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))
    
    return ('', 204)  
    

@application.route("/MeasureFP/<M>",methods=['POST'])    
def MeasureFP(M):
    #Responsible for measuring each of the active Fluorescent proteins.
    global system
    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
    for FP in ['FP1','FP2','FP3']:
        if system.sysData[M][FP]['ON']==1:
            Gain=int(system.sysData[M][FP]['Gain'][1:])
            out=GetTransmission(M,system.sysData[M][FP]['LED'],[system.sysData[M][FP]['BaseBand'],system.sysData[M][FP]['Emit1Band'],system.sysData[M][FP]['Emit2Band']],Gain,255)
            system.sysData[M][FP]['Base']=float(out[0])
            if (system.sysData[M][FP]['Base']>0):
                system.sysData[M][FP]['Emit1']=float(out[1])/system.sysData[M][FP]['Base']
                system.sysData[M][FP]['Emit2']=float(out[2])/system.sysData[M][FP]['Base']
            else:#This might happen if you try to measure in CLEAR whilst also having CLEAR as baseband! 
                system.sysData[M][FP]['Emit1']=float(out[1]) 
                system.sysData[M][FP]['Emit2']=float(out[2])

    return ('', 204)      
    

    
    
@application.route("/MeasureTemp/<which>/<M>",methods=['POST'])
def MeasureTemp(M,which): 
    #Used to measure temperature from each thermometer.
    global system
   
    if (M=="0"):
        M=system.sysItems['UIDevice']
    M=str(M)
    which='Thermometer' + str(which)
    if (which=='ThermometerInternal' or which=='ThermometerExternal'):
        getData=I2CCom(M,which,1,16,0x05,0,0)
        getDataBinary=bin(getData)
        tempData=getDataBinary[6:]
        temperature=float(int(tempData,2))/16.0
    elif(which=='ThermometerIR'):
        getData=I2CCom(M,which,1,0,0x07,0,1)
        temperature = (getData*0.02) - 273.15

    if system.sysData[M]['present']==0:
        temperature=0.0
    if temperature>100.0:#It seems sometimes the IR thermometer returns a value of 1000 due to an error. This prevents that.
        temperature=system.sysData[M][which]['current']
    system.sysData[M][which]['current']=temperature
    return ('', 204) 
    


    
def setPWM(M,device,channels,fraction,ConsecutiveFails):
    #Sets up the PWM chip (either the one in the reactor or on the pump board)
    global system
    
    if system.sysDevices[M][device]['startup']==0: #The following boots up the respective PWM device to the correct frequency. Potentially there is a bug here; if the device loses power after this code is run for the first time it may revert to default PWM frequency.
        I2CCom(M,device,0,8,0x00,0x10,0) #Turns off device. Also disables all-call functionality at bit 0 so it won't respond to address 0x70
        I2CCom(M,device,0,8,0x04,0xe6,0) #Sets SubADDR3 of the PWM chips to be 0x73 instead of 0x74 to avoid any potential collision with the multiplexer @ 0x74
        I2CCom(M,device,0,8,0xfe,system.sysDevices[M][device]['frequency'],0) #Sets frequency of PWM oscillator. 
        system.sysDevices[M][device]['startup']=1
    
    I2CCom(M,device,0,8,0x00,0x00,0) #Turns device on 
    
        
    
    timeOn=int(fraction*4095.99)
    I2CCom(M,device,0,8,channels['ONL'],0x00,0)
    I2CCom(M,device,0,8,channels['ONH'],0x00,0)
    
    OffVals=bin(timeOn)[2:].zfill(12)
    HighVals='0000' + OffVals[0:4]
    LowVals=OffVals[4:12]
    
    I2CCom(M,device,0,8,channels['OFFL'],int(LowVals,2),0)
    I2CCom(M,device,0,8,channels['OFFH'],int(HighVals,2),0)
    
    if (device=='Pumps'):
        I2CCom(M,device,0,8,channels['ONL'],0x00,0)
        I2CCom(M,device,0,8,channels['ONH'],0x00,0)
        I2CCom(M,device,0,8,channels['OFFL'],int(LowVals,2),0)
        I2CCom(M,device,0,8,channels['OFFH'],int(HighVals,2),0)
    else:
        CheckLow=I2CCom(M,device,1,8,channels['OFFL'],-1,0)
        CheckHigh=I2CCom(M,device,1,8,channels['OFFH'],-1,0)
        CheckLowON=I2CCom(M,device,1,8,channels['ONL'],-1,0)
        CheckHighON=I2CCom(M,device,1,8,channels['ONH'],-1,0)
    
        if(CheckLow!=(int(LowVals,2)) or CheckHigh!=(int(HighVals,2)) or CheckHighON!=int(0x00) or CheckLowON!=int(0x00)): #We check to make sure it has been set to appropriate values.
            ConsecutiveFails=ConsecutiveFails+1
            print(str(datetime.now()) + ' Failed transmission test on ' + str(device) + ' ' + str(ConsecutiveFails) + ' times consecutively on device '  + str(M) )
            if ConsecutiveFails>10:
                system.sysItems['Watchdog']['ON']=0 #Basically this will crash all the electronics and the software. 
                print(str(datetime.now()) + 'Failed to communicate to PWM 10 times. Disabling hardware and software!')
                os._exit(4)
            else:
                time.sleep(0.1)
                system.sysItems['FailCount']=system.sysItems['FailCount']+1
                setPWM(M,device,channels,fraction,ConsecutiveFails)
    



def csvData(M):
    #Used to format current data and write a new row to CSV file output. Note if you want to record any additional parameters/measurements then they need to be added to this function.
    global system
    M=str(M)

    fieldnames = ['exp_time','od_measured','od_setpoint','od_zero_setpoint','thermostat_setpoint','heating_rate',
                  'internal_air_temp','external_air_temp','media_temp','opt_gen_act_int','pump_1_rate','pump_2_rate',
                  'pump_3_rate','pump_4_rate','media_vol','stirring_rate','LED_395nm_setpoint','LED_457nm_setpoint',
                  'LED_500nm_setpoint','LED_523nm_setpoint','LED_595nm_setpoint','LED_623nm_setpoint',
                  'LED_6500K_setpoint','laser_setpoint','LED_UV_int','FP1_base','FP1_emit1','FP1_emit2','FP2_base',
                  'FP2_emit1','FP2_emit2','FP3_base','FP3_emit1','FP3_emit2','custom_prog_param1','custom_prog_param2',
                  'custom_prog_param3','custom_prog_status','zigzag_target','growth_rate']

    row=[system.sysData[M]['time']['record'][-1],
        system.sysData[M]['OD']['record'][-1],
        system.sysData[M]['OD']['targetrecord'][-1],
        system.sysData[M]['OD0']['target'],
        system.sysData[M]['Thermostat']['record'][-1],
        system.sysData[M]['Heat']['target']*float(system.sysData[M]['Heat']['ON']),
        system.sysData[M]['ThermometerInternal']['record'][-1],
        system.sysData[M]['ThermometerExternal']['record'][-1],
        system.sysData[M]['ThermometerIR']['record'][-1],
        system.sysData[M]['Light']['record'][-1],
        system.sysData[M]['Pump1']['record'][-1],
        system.sysData[M]['Pump2']['record'][-1],
        system.sysData[M]['Pump3']['record'][-1],
        system.sysData[M]['Pump4']['record'][-1],
        system.sysData[M]['Volume']['target'],
        system.sysData[M]['Stir']['target']*system.sysData[M]['Stir']['ON'],]
    for LED in ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']:
        row=row+[system.sysData[M][LED]['target']]
    row=row+[system.sysData[M]['UV']['target']*system.sysData[M]['UV']['ON']]
    for FP in ['FP1','FP2','FP3']:
        if system.sysData[M][FP]['ON']==1:
            row=row+[system.sysData[M][FP]['Base']]
            row=row+[system.sysData[M][FP]['Emit1']]
            row=row+[system.sysData[M][FP]['Emit2']]
        else:
            row=row+([0.0, 0.0, 0.0])
    
    row=row+[system.sysData[M]['Custom']['param1']*float(system.sysData[M]['Custom']['ON'])]
    row=row+[system.sysData[M]['Custom']['param2']*float(system.sysData[M]['Custom']['ON'])]
    row=row+[system.sysData[M]['Custom']['param3']*float(system.sysData[M]['Custom']['ON'])]
    row=row+[system.sysData[M]['Custom']['Status']*float(system.sysData[M]['Custom']['ON'])]
    row=row+[system.sysData[M]['Zigzag']['target']*float(system.sysData[M]['Zigzag']['ON'])]
    row=row+[system.sysData[M]['GrowthRate']['current']*system.sysData[M]['Zigzag']['ON']]
    
   
	#Following can be uncommented if you are recording ALL spectra for e.g. biofilm experiments
    #bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR','NIR']    
    #items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    #for item in items:
    #   for band in bands:
    #       row=row+[system.sysData[M]['biofilm'][item][band]]



    filename = system.sysData[M]['Experiment']['startTime'] + '_' + M + '_data' + '.csv'
    filename=filename.replace(":","_")

    lock.acquire() #We are avoiding writing to a file at the same time as we do digital communications, since it might potentially cause the computer to lag and consequently data transfer to fail.
    if os.path.isfile(filename) is False: #Only if we are starting a fresh file
        if (len(row) == len(fieldnames)):  #AND the fieldnames match up with what is being written.
            with open(filename, 'a') as csvFile:
                writer = csv.writer(csvFile)
                writer.writerow(fieldnames)
        else:
            print('CSV_WRITER: mismatch between column num and header num')

    with open(filename, 'a') as csvFile: # Here we append the new data to our CSV file.
        writer = csv.writer(csvFile)
        writer.writerow(row)
    csvFile.close()        
    lock.release() 
    

def downsample(M):
    #In order to prevent the UI getting too laggy, we downsample the stored data every few hours. Note that this doesnt downsample that which has already been written to CSV, so no data is ever lost.
    global system
    M=str(M)
    
    
    
    
    #We now generate a new time vector which is downsampled at half the rate of the previous one
    time=np.asarray(system.sysData[M]['time']['record'])
    newlength=int(round(len(time)/2,2)-1)
    tnew=np.linspace(time[0],time[-11],newlength)
    tnew=np.concatenate([tnew,time[-10:]])
    
    #In the following we make a new array, index, which has the indices at which we want to resample our existing data vectors.
    i=0
    index=np.zeros((len(tnew),),dtype=int)
    for timeval in tnew:
        idx = np.searchsorted(time, timeval, side="left")
        if idx > 0 and (idx == len(time) or np.abs(timeval - time[idx-1]) < np.abs(timeval - time[idx])):
            index[i]=idx-1
        else:
            index[i]=idx
        i=i+1
    
 
    system.sysData[M]['time']['record']=downsampleFunc(system.sysData[M]['time']['record'],index)
    system.sysData[M]['OD']['record']=downsampleFunc(system.sysData[M]['OD']['record'],index)
    system.sysData[M]['OD']['targetrecord']=downsampleFunc(system.sysData[M]['OD']['targetrecord'],index)
    system.sysData[M]['Thermostat']['record']=downsampleFunc(system.sysData[M]['Thermostat']['record'],index)
    system.sysData[M]['Light']['record']=downsampleFunc(system.sysData[M]['Light']['record'],index)
    system.sysData[M]['ThermometerInternal']['record']=downsampleFunc(system.sysData[M]['ThermometerInternal']['record'],index)
    system.sysData[M]['ThermometerExternal']['record']=downsampleFunc(system.sysData[M]['ThermometerExternal']['record'],index)
    system.sysData[M]['ThermometerIR']['record']=downsampleFunc(system.sysData[M]['ThermometerIR']['record'],index)
    system.sysData[M]['Pump1']['record']=downsampleFunc(system.sysData[M]['Pump1']['record'],index)
    system.sysData[M]['Pump2']['record']=downsampleFunc(system.sysData[M]['Pump2']['record'],index)
    system.sysData[M]['Pump3']['record']=downsampleFunc(system.sysData[M]['Pump3']['record'],index)
    system.sysData[M]['Pump4']['record']=downsampleFunc(system.sysData[M]['Pump4']['record'],index)
    system.sysData[M]['GrowthRate']['record']=downsampleFunc(system.sysData[M]['GrowthRate']['record'],index)
    
        
    for FP in ['FP1','FP2','FP3']:
        system.sysData[M][FP]['BaseRecord']=downsampleFunc(system.sysData[M][FP]['BaseRecord'],index)
        system.sysData[M][FP]['Emit1Record']=downsampleFunc(system.sysData[M][FP]['Emit1Record'],index)
        system.sysData[M][FP]['Emit2Record']=downsampleFunc(system.sysData[M][FP]['Emit2Record'],index)
        
def downsampleFunc(datain,index):
    #This function Is used to downsample the arrays, taking the points selected by the index vector.
    datain=list(datain)
    newdata=[]
    newdata=np.zeros((len(index),),dtype=float)

    i=0
    for loc in list(index):
        newdata[i]=datain[int(loc)]
        
        i=i+1
    return list(newdata)
    
        



def RegulateOD(M):
    #Function responsible for turbidostat functionality (OD control)
    global system
    M=str(M)
    
    if (system.sysData[M]['Zigzag']['ON']==1):
        TargetOD=system.sysData[M]['OD']['target']
        Zigzag(M) #Function that calculates new target pump rates, and sets pumps to desired rates. 

    
    Pump1Current=abs(system.sysData[M]['Pump1']['target'])
    Pump2Current=abs(system.sysData[M]['Pump2']['target'])
    Pump1Direction=system.sysData[M]['Pump1']['direction']
    Pump2Direction=system.sysData[M]['Pump2']['direction']
    
    
    
    ODNow=system.sysData[M]['OD']['current']
    ODTarget=system.sysData[M]['OD']['target']
    if (ODTarget<=0): #There could be an error on the log operationif ODTarget is 0!
        ODTarget=0.000001
        
    errorTerm=ODTarget-ODNow
    Volume=system.sysData[M]['Volume']['target']
    
    PercentPerMin=4*60/Volume #Gain parameter to convert from pump rate to rate of OD reduction.

    if system.sysData[M]['Experiment']['cycles']<3:
        Pump1=0 #In first few cycles we do precisely no pumping.
    elif len(system.sysData[M]['time']['record']) < 2:
        Pump1=0 #In first few cycles we do precisely no pumping.
        addTerminal(M, "Warning: Tried to calculate time elapsed with fewer than two " +\
    				"timepoints recorded. If you see this message a lot, there may be " +\
    				"a more serious problem.")
    else:
        ODPast=system.sysData[M]['OD']['record'][-1]
        timeElapsed=((system.sysData[M]['time']['record'][-1])-(system.sysData[M]['time']['record'][-2]))/60.0 #Amount of time betwix measurements in minutes
        if (ODNow>0):
            try:
                NewGrowth = math.log((ODTarget)/(ODNow))/timeElapsed
            except:
                NewGrowth=0.0
        else:
            NewGrowth=0.0
            
        Pump1=-1.0*NewGrowth/PercentPerMin
        
        #Next Section is Integral Control
        ODerror=ODNow-ODTarget
        # Integrator 1 - resoponsible for short-term integration to overcome troubles if an input pump makes a poor seal.
        ODIntegral=system.sysData[M]['OD']['Integral']
        if ODerror<0.01:
            ODIntegral=0
        elif (abs(ODNow-ODPast)<0.05 and ODerror>0.025): #preventing massive accidental jumps causing trouble with this integral term.
            ODIntegral=ODIntegral+0.1*ODerror
        system.sysData[M]['OD']['Integral']=ODIntegral
        # Integrator 2 
        ODIntegral2=system.sysData[M]['OD']['Integral2']
        if (abs(ODerror)>0.1 and abs(ODNow-ODPast)<0.05):
            ODIntegral2=0
        elif (abs(ODNow-ODPast)<0.1):
            ODIntegral2=ODIntegral2+0.01*ODerror
            Pump1=Pump1*0.7 #This is essentially enforcing a smaller Proportional gain when we are near to OD setpoint.
        system.sysData[M]['OD']['Integral2']=ODIntegral2
        
        Pump1=Pump1+ODIntegral+ODIntegral2
        
        if (ODNow-ODPast)>0.04: #This is to counteract noisy jumps in OD measurements from causing mayhem in the regulation algorithm.
            Pump1=0.0

    #Make sure values are in appropriate range. We want to limit the maximum size of pump1 to prevent it from overflowing.
    if(Pump1>0.02):
        Pump1=0.02
    elif(Pump1<0):
        Pump1=0.0

    if(system.sysData[M]['Chemostat']['ON']==1):
        Pump1=float(system.sysData[M]['Chemostat']['p1'])

    #Set new Pump targets
    system.sysData[M]['Pump1']['target']=Pump1*Pump1Direction
    system.sysData[M]['Pump2']['target']=(Pump1*4+0.07)*Pump2Direction

    if(system.sysData[M]['Experiment']['cycles']%5==1): #Every so often we do a big output pump to make sure tubes are clear.
        system.sysData[M]['Pump2']['target']=0.25*system.sysData[M]['Pump2']['direction']
    
    
    
    
    if (system.sysData[M]['Experiment']['cycles']>15):
        #This section is to check if we have added any liquid recently, if not, then we dont run pump 2 since it won't be needed.
        pastpumping=abs(system.sysData[M]['Pump1']['target'])
        for pv in range(-10,-1):
            pastpumping=pastpumping+abs(system.sysData[M]['Pump1']['record'][pv])
        
        if pastpumping==0.0:
            system.sysData[M]['Pump2']['target']=0.0
            system.sysData[M]['Pump1']['target']=0.0 #This should be equal to 0 anyway.
        
        

    SetOutputOn(M,'Pump1',1)
    SetOutputOn(M,'Pump2',1)

        
    if (system.sysData[M]['Zigzag']['ON']==1): #If the zigzag growth estimation is running then we change OD setpoint appropriately.
        try:
            system.sysData[M]['OD']['target']=TargetOD
        except:
            print('Somehow you managed to activate Zigzag at a sub-optimal time')
            #Do nothing
 
    return
    
def Zigzag(M):
    #This function dithers OD in a "zigzag" pattern, and estimates growthrate. This function is only called when ZigZag mode is active.
    global system

    M=str(M)
    centre=system.sysData[M]['OD']['target']
    current=system.sysData[M]['OD']['current']
    zig=system.sysData[M]['Zigzag']['Zig']
    iteration=system.sysData[M]['Experiment']['cycles']
	
    try:
        last=system.sysData[M]['OD']['record'][-1]
    except: #This will happen if you activate Zigzag in first control iteration!
        last=current
    
    if (current<centre-zig and last<centre):
        if(system.sysData[M]['Zigzag']['target']!=5.0):
            system.sysData[M]['Zigzag']['SwitchPoint']=iteration
        system.sysData[M]['Zigzag']['target']=5.0 #an excessively high OD value.
    elif (current>centre+zig and last>centre+zig):
        system.sysData[M]['Zigzag']['target']=centre-zig*1.5
        system.sysData[M]['Zigzag']['SwitchPoint']=iteration

    system.sysData[M]['OD']['target']=system.sysData[M]['Zigzag']['target']
	
    #Subsequent section is for growth estimation.
	
    TimeSinceSwitch=iteration-system.sysData[M]['Zigzag']['SwitchPoint']
    if (iteration>6 and TimeSinceSwitch>5 and current > 0 and last > 0 and system.sysData[M]['Zigzag']['target']==5.0): #The reason we wait a few minutes after starting growth is that new media may still be introduced, it takes a while for the growth to get going.
        dGrowthRate=(math.log(current)-math.log(last))*60.0 #Converting to units of 1/hour
        system.sysData[M]['GrowthRate']['current']=system.sysData[M]['GrowthRate']['current']*0.95 + dGrowthRate*0.05 #We are essentially implementing an online growth rate estimator with learning rate 0.05

    return



@application.route("/ExperimentReset",methods=['POST'])
def ExperimentReset():
    #Resets parameters/values of a given experiment.
    initialise(system.sysItems['UIDevice'])
    return ('', 204)   

@application.route("/Experiment/<value>/<M>",methods=['POST'])
def ExperimentStartStop(M,value):
    #Stops or starts an experiment. 
    global system

    M=str(M)
    if (M=="0"):
        M=system.sysItems['UIDevice']
       
    value=int(value)
    #Turning it on involves keeping current pump directions,
    if (value and (system.sysData[M]['Experiment']['ON']==0)):
        
        system.sysData[M]['Experiment']['ON']=1
        addTerminal(M,'Experiment Started')
        
        if (system.sysData[M]['Experiment']['cycles']==0):
            now=datetime.now()
            timeString=now.strftime("%Y-%m-%d %H:%M:%S")
            system.sysData[M]['Experiment']['startTime']=timeString
            system.sysData[M]['Experiment']['startTimeRaw']=now
        
        system.sysData[M]['Pump1']['direction']=1.0 #Sets pumps to go forward.
        system.sysData[M]['Pump2']['direction']=1.0

        turn_everything_off(M)
        
        SetOutputOn(M,'Thermostat',1)
        system.sysDevices[M]['Experiment']=Thread(target = runExperiment, args=(M,'placeholder'))
        system.sysDevices[M]['Experiment'].setDaemon(True)
        system.sysDevices[M]['Experiment'].start()
        
    else:
        system.sysData[M]['Experiment']['ON']=0
        system.sysData[M]['OD']['ON']=0
        addTerminal(M,'Experiment Stopping at end of cycle')
        SetOutputOn(M,'Pump1',0)
        SetOutputOn(M,'Pump2',0)
        SetOutputOn(M,'Stir',0)
        SetOutputOn(M,'Thermostat',0)
        
    return ('', 204)
    
    
    
def runExperiment(M,placeholder):
    #Primary function for running an automated experiment.
    M=str(M)
   
    global system

    
    system.sysData[M]['Experiment']['threadCount']=(system.sysData[M]['Experiment']['threadCount']+1)%100
    currentThread=system.sysData[M]['Experiment']['threadCount']
        
    # Get time running in seconds
    now=datetime.now()
    elapsedTime=now-system.sysData[M]['Experiment']['startTimeRaw']
    elapsedTimeSeconds=round(elapsedTime.total_seconds(),2)
    system.sysData[M]['Experiment']['cycles']=system.sysData[M]['Experiment']['cycles']+1
    addTerminal(M,'Cycle ' + str(system.sysData[M]['Experiment']['cycles']) + ' Started')
    CycleTime=system.sysData[M]['Experiment']['cycleTime']

    SetOutputOn(M,'Stir',0) #Turning stirring off
    time.sleep(5.0) #Wait for liquid to settle.
    if (system.sysData[M]['Experiment']['ON']==0):
        turn_everything_off(M)
        system.sysData[M]['Experiment']['cycles']=system.sysData[M]['Experiment']['cycles']-1 # Cycle didn't finish, don't count it.
        addTerminal(M,'Experiment Stopped')
        return
    
    system.sysData[M]['OD']['Measuring']=1 #Begin measuring - this flag is just to indicate that a measurement is currently being taken.
    
    #We now meausre OD 4 times and take the average to reduce noise when in auto mode!
    ODV=0.0
    for i in [0, 1, 2, 3]:
        MeasureOD(M)
        ODV=ODV+system.sysData[M]['OD']['current']
        time.sleep(0.25)
    system.sysData[M]['OD']['current']=ODV/4.0
    
    MeasureTemp(M,'Internal') #Measuring all temperatures
    MeasureTemp(M,'External')
    MeasureTemp(M,'IR')
    MeasureFP(M) #And now fluorescent protein concentrations. 
	
    if (system.sysData[M]['Experiment']['ON']==0): #We do another check post-measurement to see whether we need to end the experiment.
        turn_everything_off(M)
        system.sysData[M]['Experiment']['cycles']=system.sysData[M]['Experiment']['cycles']-1 # Cycle didn't finish, don't count it.
        addTerminal(M,'Experiment Stopped')
        return
    #Temporary Biofilm Section - the below makes the device all spectral data for all LEDs each cycle.
    
    # bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR','NIR']    
    # items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    # gains=['x10','x10','x10','x10','x10','x10','x10','x1']
    # gi=-1
    # for item in items:
    #     gi=gi+1
    #     SetOutputOn(M,item,1)
    #     GetSpectrum(M,gains[gi])
    #     SetOutputOn(M,item,0)
    #     for band in bands:
    #         system.sysData[M]['biofilm'][item][band]=int(system.sysData[M]['AS7341']['spectrum'][band])

    system.sysData[M]['OD']['Measuring']=0
    if (system.sysData[M]['OD']['ON']==1):
        RegulateOD(M) #Function that calculates new target pump rates, and sets pumps to desired rates. 
    
    LightActuation(M,1) 
    
    if (system.sysData[M]['Custom']['ON']==1): #Check if we have enabled custom programs
        CustomThread=Thread(target = CustomProgram, args=(M,)) #We run this in a thread in case we are doing something slow, we dont want to hang up the main l00p. The comma after M is to cast the args as a tuple to prevent it iterating over the thread M
        CustomThread.setDaemon(True)
        CustomThread.start()

    
    Pump2Ontime=system.sysData[M]['Experiment']['cycleTime']*1.05*abs(system.sysData[M]['Pump2']['target'])*system.sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
    time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
    
    SetOutputOn(M,'Stir',1) #Start stirring again.

    if(system.sysData[M]['Experiment']['cycles']%10==9): #Dont want terminal getting unruly, so clear it each 10 rotations.
        clearTerminal(M)
    
    #######Below stores all the results for plotting later
    system.sysData[M]['time']['record'].append(elapsedTimeSeconds)
    system.sysData[M]['OD']['record'].append(system.sysData[M]['OD']['current'])
    system.sysData[M]['OD']['targetrecord'].append( system.sysData[M]['OD']['target']*system.sysData[M]['OD']['ON'])
    system.sysData[M]['Thermostat']['record'].append(system.sysData[M]['Thermostat']['target']*float(system.sysData[M]['Thermostat']['ON']))
    system.sysData[M]['Light']['record'].append(float(system.sysData[M]['Light']['ON']))
    system.sysData[M]['ThermometerInternal']['record'].append(system.sysData[M]['ThermometerInternal']['current'])
    system.sysData[M]['ThermometerExternal']['record'].append(system.sysData[M]['ThermometerExternal']['current'])
    system.sysData[M]['ThermometerIR']['record'].append(system.sysData[M]['ThermometerIR']['current'])
    system.sysData[M]['Pump1']['record'].append(system.sysData[M]['Pump1']['target']*float(system.sysData[M]['Pump1']['ON']))
    system.sysData[M]['Pump2']['record'].append(system.sysData[M]['Pump2']['target']*float(system.sysData[M]['Pump2']['ON']))
    system.sysData[M]['Pump3']['record'].append(system.sysData[M]['Pump3']['target']*float(system.sysData[M]['Pump3']['ON']))
    system.sysData[M]['Pump4']['record'].append(system.sysData[M]['Pump4']['target']*float(system.sysData[M]['Pump4']['ON']))
    system.sysData[M]['GrowthRate']['record'].append(system.sysData[M]['GrowthRate']['current']*float(system.sysData[M]['Zigzag']['ON']))
    for FP in ['FP1','FP2','FP3']:
        if system.sysData[M][FP]['ON']==1:
            system.sysData[M][FP]['BaseRecord'].append(system.sysData[M][FP]['Base'])
            system.sysData[M][FP]['Emit1Record'].append(system.sysData[M][FP]['Emit1'])
            if (system.sysData[M][FP]['Emit2Band']!= "OFF"):
                system.sysData[M][FP]['Emit2Record'].append(system.sysData[M][FP]['Emit2'])
            else:
                system.sysData[M][FP]['Emit2Record'].append(0.0)
        else:
            system.sysData[M][FP]['BaseRecord'].append(0.0)
            system.sysData[M][FP]['Emit1Record'].append(0.0)
            system.sysData[M][FP]['Emit2Record'].append(0.0)
    
    #We  downsample our records such that the size of the data vectors being plot in the web interface does not get unruly. 
    if (len(system.sysData[M]['time']['record'])>200):
        downsample(M)

    #### Writing Results to data files
    csvData(M) #This command writes system data to a CSV file for future keeping.
    #And intermittently write the setup parameters to a data file. 
    if(system.sysData[M]['Experiment']['cycles']%10==1): #We only write whole configuration file each 10 cycles since it is not really that important. 
        TempStartTime=system.sysData[M]['Experiment']['startTimeRaw']
        system.sysData[M]['Experiment']['startTimeRaw']=0 #We had to set this to zero during the write operation since the system does not like writing data in such a format.
        
        filename = system.sysData[M]['Experiment']['startTime'] + '_' + M + '.txt'
        filename=filename.replace(":","_")
        f = open(filename,'w')
        simplejson.dump(system.sysData[M],f)
        f.close()
        system.sysData[M]['Experiment']['startTimeRaw']=TempStartTime
    ##### Written

    if (system.sysData[M]['Experiment']['ON']==0):
        turn_everything_off(M)
        addTerminal(M,'Experiment Stopped')
        return
    
    nowend=datetime.now()
    elapsedTime2=nowend-now
    elapsedTimeSeconds2=round(elapsedTime2.total_seconds(),2)
    sleeptime=CycleTime-elapsedTimeSeconds2
    if (sleeptime<0):
        sleeptime=0
        addTerminal(M,'Experiment Cycle Time is too short!!!')    
        
    time.sleep(sleeptime)
    LightActuation(M,0) #Turn light actuation off if it is running.
    addTerminal(M,'Cycle ' + str(system.sysData[M]['Experiment']['cycles']) + ' Complete')

    #Now we run this function again if the automated experiment is still going.
    if (system.sysData[M]['Experiment']['ON'] and system.sysData[M]['Experiment']['threadCount']==currentThread):
        system.sysDevices[M]['Experiment']=Thread(target = runExperiment, args=(M,'placeholder'))
        system.sysDevices[M]['Experiment'].setDaemon(True)
        system.sysDevices[M]['Experiment'].start()
        
    else: 
        turn_everything_off(M)
        addTerminal(M,'Experiment Stopped')
   



if __name__ == '__main__':
    initialiseAll()
    application.run(debug=True,threaded=True,host='0.0.0.0',port=5000)
    
initialiseAll()
print(str(datetime.now()) + ' Start Up Complete')
