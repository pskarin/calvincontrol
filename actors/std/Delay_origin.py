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

    @manage(['timer', 'delay', 'started'])
    def init(self, delay_data="/tmp/data.txt"):
        self.delay = 0
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.started = False
        self.path = delay_data
        self.seq = []
        self.dl = []
        self.counter = 0
        self.packetloss = False
        self.setup()
        self.token = None

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
    
    def new_timer(self):
        timer = calvinsys.open(self, "sys.timer.once")
        return timer

    @stateguard(lambda self: (not self.started
                              and calvinsys.can_write(self.timer)))
    @condition(['token', 'tick'], [])
    def start_timer(self, token, tick):
        #_log.info("Start new timer")
        self.token = token
        self.started = True
        self.delay = 0
        self.packetloss = True
        if len(self.seq) > self.counter:
            sq = self.seq[self.counter]
           # _log.info('Sq: {}, tick: {}'.format(sq, tick))
            if sq == tick:
                self.delay = self.dl[self.counter]/2
                self.counter += 1
                self.packetloss = False

       # _log.warning('Delay: {}'.format(self.delay))
        calvinsys.write(self.timer, self.delay)

    @stateguard(lambda self: (calvinsys.can_read(self.timer)
                              and not self.packetloss))
    @condition([], ['token'])
    def passthrough(self):
        _log.warning('Delay: passthrough')
        self.started = False
        #_log.info("Token: {}".format(self.token))
        calvinsys.read(self.timer)
        return (self.token, )

    @stateguard(lambda self: (calvinsys.can_read(self.timer)
                              and self.packetloss))
    @condition([], [])
    def droptocken(self):
        _log.warning('Delay: drop packet')
        self.started = False
        calvinsys.read(self.timer)

    action_priority = (start_timer, passthrough, droptocken, )
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
