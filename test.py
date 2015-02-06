"""
    Code based on:
        https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/03-basicchannel.py
    in the python-ant repository and
        https://github.com/tomwardill/developerhealth
    by Tom Wardill
"""
import sys
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER

#candence_cnt = 0
#candence_time = 0
#candence_cnt_old = -1
#candence_time_old = -1
class HRM(event.EventCallback):

    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None
        self.cadence_cnt = 0
        self.cadence_time = 0
        self.cadence_cnt_old = -1
        self.cadence_time_old = -1
        self.cadence = 0
        self.speed_cnt=0
        self.speed_time=0
        self.speed_cnt_old=-1
        self.speed_time_old=-1
        self.speed=0
        self.switch=1
        self.heartrate=60

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(self)
        print("start listening for cadence events")

    def stop(self):
        if self.channel:
            self.channel.close()
            self.channel.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver(self.serial)
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
        self.antnode.setNetworkKey(0, key)
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:HRM'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(120, 0, 0)
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
        self.channel.setPeriod(8070)
        self.channel.setFrequency(57)
        self.channel.open()

    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            if self.switch==1:
                #print("heart rate is {}".format(ord(msg.payload[-1])))
                self.heartrate=int(ord(msg.payload[-1]))
            #print ord(msg.payload[2])A
            #print ord(msg.payload[3])
            else:
                self.cadence_cnt = int(ord(msg.payload[3]))+256*ord(msg.payload[4])
                #print '================================='
                #print self.cadence_cnt
                self.cadence_time = ord(msg.payload[1])+256*ord(msg.payload[2])
                #print self.cadence_time/1024.0
                if self.cadence_time == self.cadence_time_old:
                    #self.cadence = 0
                    return
                if self.cadence_cnt_old == -1:
                    self.cadence_cnt_old = self.cadence_cnt
                    self.cadence_time_old = self.cadence_time
                    return
                if self.cadence_cnt < self.cadence_cnt_old:
                    self.cadence_cnt += 65536
                if self.cadence_time < self.cadence_time_old:
                    self.cadence_time += 65536
                self.cadence=(self.cadence_cnt-self.cadence_cnt_old)*1024*60.0/(self.cadence_time-self.cadence_time_old)
                #print "cadence="+str(self.cadence)
                if self.cadence_time > 65536:
                    self.cadence_time -= 65536
                if self.cadence_cnt > 65536:
                    self.cadence_cnt -= 65536
                self.cadence_cnt_old = self.cadence_cnt
                self.cadence_time_old = self.cadence_time
                self.speed_cnt=int(ord(msg.payload[-2])+256*ord(msg.payload[-1]))
                #print self.speed_cnt
                self.speed_time=int(ord(msg.payload[-4])+256*ord(msg.payload[-3]))
                #print self.speed_time
                if self.speed_cnt_old==-1:
                    self.speed_cnt_old=self.speed_cnt
                    self.speed_time_old=self.speed_time
                    return
                #if self.speed_time_old == self.speed_time:
                #    self.speed = 0
                if self.speed_cnt<self.speed_cnt_old:
                    self.speed_cnt+=65536
                if self.speed_time<self.speed_time_old:
                    self.speed_time+=65536
                #self.speed=(self.speed_cnt-self.speed_cnt_old)*1024*60.0/(self.speed_time-self.speed_time_old)
                self.speed=2.07*3.6*(self.speed_cnt-self.speed_cnt_old)*1024/(self.speed_time-self.speed_time_old)
                #print "speed="+str(self.speed)
                if self.speed_cnt>65536:
                    self.speed_cnt-=65536
                if self.speed_time>65536:
                    self.speed_time-=65536
                self.speed_cnt_old=self.speed_cnt
                self.speed_time_old=self.speed_time 




SERIAL = '/dev/ttyUSB0'
NETKEY = 'B9A521FBBD72C345'.decode('hex')

hrm = HRM(serial=SERIAL, netkey=NETKEY)
hrm.start()

cadence_stop_pre=0
speed_stop_pre=0
stop_cnt=0
while True:
        try:
            time.sleep(0.1)
            print "================"
            print "cadence: "+str(hrm.cadence)
            print "speed: "+str(hrm.speed)
            print "heart rate: "+str(hrm.heartrate)
            if stop_cnt==0:
                cadence_stop_pre=hrm.cadence
                speed_stop_pre=hrm.speed
                print 'pre:'+str(cadence_stop_pre)
            stop_cnt=stop_cnt+1
            if stop_cnt==4:
                stop_cnt=0
                print 'now: '+str(hrm.cadence)+' pre:'+str(cadence_stop_pre)
                if int(hrm.cadence)==int(cadence_stop_pre):
                    print 'ca stop!'
                    hrm.cadence=0
                if int(hrm.speed)==int(speed_stop_pre):
                    print 'speed stop!'
                    hrm.speed=0
            if hrm.switch==1:
                hrm.channel.close()
                hrm.channel.setID(121, 0, 0)
                hrm.channel.setPeriod(8086)
                hrm.channel.open()
                hrm.switch=-1
            else:
                hrm.channel.close()
                hrm.channel.setID(120, 0, 0)
                hrm.channel.setPeriod(8070)
                hrm.channel.open()
                hrm.switch=1
        except KeyboardInterrupt:
            sys.exit(0)
    
#with HRM(serial=SERIAL, netkey=NETKEY) as hrm:
#    hrm.start()
#    while True:
#        try:
#            time.sleep(1)
#        except KeyboardInterrupt:
#            sys.exit(0)
