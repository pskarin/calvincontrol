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
from calvin.utilities.calvinlogger import get_actor_logger
_log = get_actor_logger(__name__)


class Delay(Actor):
    """
    After first token, pass on token once every 'delay' seconds.
    Input :
        tick: counter
        token: anything
    Outputs:
        token: anything
    """

    @manage(['timer', 'delay'])
    def init(self, delay_data="/tmp/data.txt"):
        self.delay = 0
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.time = self['time']
        #self.started = False
        self.path = delay_data
        self.seq = []
        self.dl = []
        self.counter = 1
        self.packetloss = False
        self.last_input = None
        self.last_output = None
        self.delay_list = []
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
            _log.info("Delay sequence length: {}".format(len(self.seq)))
            f.close()
        except IOError as err:
            _log.error(err)
            pass

    #start the
    #@stateguard(lambda self: (not self.started
    #                          and calvinsys.can_write(self.timer)))
    @condition(['token', 'tick'], [])
    def token_available(self, token, tick):
        _log.info("New token arrives")
        #self.started = True
        self.delay = 0
        self.packetloss = True
        if len(self.seq) > self.counter:
            sq = self.seq[self.counter]
           # _log.info('Sq: {}, tick: {}'.format(sq, tick))
            if sq == tick:
                self.delay = self.dl[self.counter]/2
                self.counter += 1
                self.packetloss = False
                if len(self.delay_list) > 0:
                    duration = self.last_input - self.time.timestamp()
                    self.delay_list['delay'] = [x - duration for x in self.delay_list['delay']]
                # append the new arrives in to the list and find the one be output firstly
                self.delay_list.append({'token': token, 'delay': self.delay})
                self.delay_list = sorted(self.delay_list, key=lambda k: k['delay'])
                if not calvinsys.can_write(self.timer):
                    calvinsys.read(self.timer)
                calvinsys.write(self, self.delay_list[0]['delay'])
        self.last_input = self.time.timestamp()

    @stateguard(lambda self: (calvinsys.can_read(self.timer)
                              and not self.packetloss))
    @condition([], ['token'])
    def passthrough(self):
        _log.warning('Delay: passthrough')
        item = self.delay_list.pop(0)
        calvinsys.read(self.timer)
        if len(self.delay_list) > 0:
            delay_list = [for ...]    ##unfinished yet, a new timer should be set
        return (item['token'], )

    @stateguard(lambda self: self.packetloss)
    @condition([], [])
    def droptocken(self):
        _log.warning('Delay: drop packet')
        return

    action_priority = (passthrough, droptocken, token_available, )
    requires = ['sys.timer.once']

# test_kwargs = {'delay': 20}
# test_calvinsys = {'sys.timer.repeating': {'read': ["d", "u", "m", "m", "y"],
#                                           'write': [20]}}
# test_set = [
#     {
#         'inports': {'token': ["a", "b", 1]},
#         'outports': {'token': ["a", "b", 1]}
#     }
# ]
