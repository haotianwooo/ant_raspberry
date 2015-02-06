"""
Extending on demo-03, implements an event callback we can use to process the
incoming data.

"""

import sys
import time
import serial
import RPi.GPIO as GPIO

from ant.core import driver
from ant.core import node
from ant.core import event
from ant.core import message
from ant.core.constants import *

from config import *
ser=serial.Serial()
ser.port='/dev/ttyAMA0'
ser.open()
GPIO.setmode(GPIO.BCM)
LED=5
GPIO.setup(LED,GPIO.OUT)
GPIO.output(LED,True)
heartpin=4
GPIO.setup(heartpin,GPIO.OUT)
HPWM=GPIO.PWM(heartpin,1)
HPWM.start(50)


NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'
cadence_cnt=0
cadence_time=0
cadence_cnt_old=-1
cadence_time_old=-1
cadence=0
speed_cnt=0
speed_time=0
speed_cnt_old=-1
speed_time_old=-1
speed=0
heartrate=60
# A run-the-mill event listener
class CNSListener(event.EventCallback):
    def process(self, msg):
        global cadence_cnt
        global cadence_time
        global cadence_cnt_old
        global cadence_time_old
        global cadence
        global speed_cnt
        global speed_time
        global speed_cnt_old
        global speed_time_old
        global speed

        if isinstance(msg, message.ChannelBroadcastDataMessage):
            #print 'Cadence:', ord(msg.payload[-1])
            cadence_cnt=int(ord(msg.payload[3]))+256*ord(msg.payload[4])
            cadence_time=ord(msg.payload[1])+256*ord(msg.payload[2])
            if cadence_cnt!=cadence_cnt_old:
                GPIO.output(LED,False)
                time.sleep(0.01)
                GPIO.output(LED,True)
            if cadence_cnt==cadence_cnt_old:
#                cadence=0
                return
            if cadence_time==cadence_time_old:
 #               cadence=0
                return
            if cadence_cnt_old==-1:
                cadence_cnt_old=cadence_cnt
                cadence_time_old=cadence_time
                return
            if cadence_cnt<cadence_cnt_old:
                cadence_cnt+=65536
            if cadence_time<cadence_time_old:
                cadence_time+=65536
            cadence=(cadence_cnt-cadence_cnt_old)*1024*60.0/(cadence_time-cadence_time_old)
            if cadence_cnt>65535:
                cadence_cnt-=65536
            if cadence_time>65535:
                cadence_time-=65536
            cadence_cnt_old=cadence_cnt
            cadence_time_old=cadence_time

            speed_cnt=int(ord(msg.payload[-2]))+256*ord(msg.payload[-1])
            speed_time=int(ord(msg.payload[-4]))+256*ord(msg.payload[-3])
            if speed_cnt==speed_cnt_old:
  #              speed=0
                return
            if speed_time==speed_time_old:
   #             speed=0
                return
            if speed_cnt_old==-1:
                speed_cnt_old=speed_cnt
                speed_time_old=speed_time
                return
            if speed_cnt<speed_cnt_old:
                speed_cnt+=65536
            if speed_time<speed_time_old:
                speed_time+=65536
            speed=2.07*3.6*(speed_cnt-speed_cnt_old)*1024/(speed_time-speed_time_old)
            if speed_cnt>65535:
                speed_cnt-=65536
            if speed_time>65535:
                speed_time-=65536
            speed_cnt_old=speed_cnt
            speed_time_old=speed_time

            

class HRMListener(event.EventCallback):
    def process(self, msg):
        global heartrate
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            #print 'Heart Rate:', ord(msg.payload[-1])
            heartrate=ord(msg.payload[-1])

# Initialize
stick = driver.USB2Driver(SERIAL, log=LOG, debug=DEBUG)
antnode = node.Node(stick)
antnode.start()

# Setup channel
key = node.NetworkKey('N:ANT+', NETKEY)
antnode.setNetworkKey(0, key)
channel = antnode.getFreeChannel()
channel.name = 'C:HRM'
channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
channel.setID(120, 0, 0)
channel.setSearchTimeout(TIMEOUT_NEVER)
channel.setPeriod(8070)
channel.setFrequency(57)
channel.open()

channel_1 = antnode.getFreeChannel()
channel_1.name = 'C:CNS'
channel_1.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
channel_1.setID(121, 0, 0)
channel_1.setSearchTimeout(TIMEOUT_NEVER)
channel_1.setPeriod(8086)
channel_1.setFrequency(57)
channel_1.open()

# Setup callback
# Note: We could also register an event listener for non-channel events by
# calling registerEventListener() on antnode rather than channel.
channel.registerCallback(HRMListener())
channel_1.registerCallback(CNSListener())

# Wait
print "Listening for HR monitor events (120 seconds)..."
stop_cnt=0
stop_cadence_cnt_pre=0
stop_speed_cnt_pre=0

while 1:
    if stop_cnt==0:
        stop_cadence_cnt_pre=cadence_cnt
        stop_speed_cnt_pre=speed_cnt
    stop_cnt+=1
    if stop_cnt==3:
        stop_cnt=0
        if stop_cadence_cnt_pre==cadence_cnt:
            cadence=0
        if stop_speed_cnt_pre==speed_cnt:
            speed=0

    print 'Cadence:'+str(int(cadence))+' Speed:'+str(int(speed))+' Heart Rate:'+str(heartrate)
    time.sleep(2)
    ser.write(str(int(cadence))+','+str(int(speed))+','+str(heartrate))
    HPWM.ChangeFrequency(heartrate/60.0)
#time.sleep(120)

# Shutdown
channel.close()
channel.unassign()
channel_1.close()
channel_1.unassign()
antnode.stop()
