# -*- coding: utf-8 -*-

# Copyright (c) 2015 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys
import sys
import operator
from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)


class Delay(Actor):
    """
    After first token, pass on token once every 'delay' seconds.
    Input :
        token: anything
    Outputs:
        token: anything
    """

    @manage(['timer', 'delay', 'name'])
    def init(self, delay_data="/tmp/data.txt", name_serial=1):
        self.name = None
        self.delay = 0.
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']
        self.path = delay_data
        self.seq = []
        self.dl = []
        # self.counter = 0
        self.timer_stop = None
        self.last_timer_stop = None
        self.recent_tokenin = None
        self.delay_list = []
        self.ToWrite = True
        self.ToRead = False
        self.set_name(name_serial)
        _log.info("I am {} actor.".format(self.name))
        self.setup()

    #Read the file of delays and get the delay mesurements
    def setup(self):
        try:
            f = open(self.path, 'r')
            # Read the timestamp,delay and seq number from the file
            for line in f.readlines():
                    s = int(line.split(",")[0])
                    self.seq.append(s)
                    d = float(line.split(",")[1])/1000.0
                    self.dl.append(d)
            #_log.info("Delay sequence length: {}".format(len(self.seq)))
            f.close()
        except IOError as err:
            _log.error(err)
            pass

    def set_name(self, name):
        if name == 1:
            self.name = "OuterDelay"
        if name == 2:
            self.name = "InnerDelay"
        if name == 3:
            self.name = "ActDelay"
        if name == 4:
            self.name = "OuterBack"
        if name == 5:
            self.name = "InnerBack"

    #@stateguard(lambda self: self.ToWrite and not self.ToRead)
    @condition(['token'], [])
    def token_available(self, token):
        clock_info = token[1]
        tick = clock_info[1]
        #_,clock_info,_ = token
        #_,tick,_,_,_ = clock_info
        _log.info("{}: Token arrives at tick: {} ".format(self.name, tick))
        self.timer_stop = self.time.timestamp()
        self.recent_tokenin = self.timer_stop
        self.delay = 0
        if len(self.seq) > 0:
            #sq = self.seq[self.counter]
            #_log.info("{}: Available sequence no.{}".format(self.name, sq))
            if len(self.delay_list) > 0:
                _log.info("{}: Still holding {} tokens in the list".format(self.name, len(self.delay_list)))
                duration = self.timer_stop - self.last_timer_stop
                #_log.info("Decrease time_out value with {}.".format(duration))
                for x in self.delay_list:
                    x['delay'] -= duration
                #_log.info("The least delay is {}".format(self.delay_list[0]['delay']))
            #if sq == tick:
            try:
                sq_index = self.seq.index(tick)
            except:
                _log.info("{}: Packet loss".format(self.name))
                self.last_timer_stop = self.time.timestamp()
                return

            self.delay = self.dl[sq_index] / 2
            self.dl.pop(sq_index)
            self.seq.pop(sq_index)

            self.delay_list.append({'token': token, 'delay': self.delay, 'tick': tick})
            self.delay_list = sorted(self.delay_list, key=lambda k: k['delay'])
                #_log.info("my delay list: {}".format(self.delay_list))

            #reset timer no matter the packet is dropped or not
            if not calvinsys.can_write(self.timer):
                calvinsys.read(self.timer)
                calvinsys.close(self.timer)
                #_log.info("Stop the timer before writing a new one")
            #_log.info("Write new time-out value: {}".format(self.delay))
            self.last_timer_stop = self.time.timestamp()
        #if self.delay > self.UpperMargin:
         #   self.ToWrite = True
          #  self.ToRead = False
           # _log.info("Stay in tokenavailable")
        #else:
           # self.ToWrite = False
           # self.ToRead = True
            #_log.info("Go to passthrough")
        #_log.info("Time used for setting the timer: {}".format(self.time.timestamp() - self.timer_stop))
            calvinsys.write(self.timer, self.delay)

    #@stateguard(lambda self: self.ToRead and not self.ToWrite and calvinsys.can_read(self.timer))
    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['token'])
    def passthrough(self):
        _log.warning('{}: passthrough'.format(self.name))
        calvinsys.read(self.timer)
        item = self.delay_list.pop(0)
        #_log.info("Send out packet at tick {}".format(item['tick']))
        self.timer_stop = self.time.timestamp()
        self.ToWrite = True
        self.ToRead = False
        if len(self.delay_list) > 0:
            #_log.info("Delay list not clean")
            duration = self.timer_stop - self.last_timer_stop
            for x in self.delay_list:
                x['delay'] -= duration
            self.delay = self.delay_list[0]['delay']
            if self.delay < 0:
                self.delay = 0
            #_log.info("Write new delay for rest tokens {}".format(self.delay))
            #if self.recent_tokenin + self.LowerMargin - self.timer_stop > self.delay:
             #   self.ToWrite = False
              #  self.ToRead = True
               # _log.info("Next is waited to be sent out, stay in read")
            #else:
             #   _log.info("Wait for a new token")
            calvinsys.write(self.timer, self.delay)
        self.last_timer_stop = self.time.timestamp()
        return (item['token'], )

    action_priority = (passthrough, token_available, )
    requires = ['sys.timer.once']

