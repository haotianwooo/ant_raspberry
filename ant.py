"""
Read data from cadence, speed and heart rate sensors by ANT+
Transmit data to arduino nano through serial ttyAMA0

By Haotian @5,Mar,2015
"""

import sys
import time

from ant.core import driver
from ant.core import node
from ant.core import event
from ant.core import message
from ant.core.constants import *

from config import *

NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'

cadence = 0

# A run-the-mill event listener
class CNSListener(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            cadence=888
            print 'Cadence:'+str(cadence)
            #print 'Cadence:', ord(msg.payload[-1])

class HRMListener(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print 'Heart Rate:', ord(msg.payload[-1])

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
while 1:
    pass
#time.sleep(120)

# Shutdown
channel.close()
channel.unassign()
channel_1.close()
channel_1.unassign()
antnode.stop()
