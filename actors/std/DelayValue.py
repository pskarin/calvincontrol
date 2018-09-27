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
    def init(self):
        self.name = "Smith Delay"
        self.delay = 0.
        self.timer = None
        self.seq = []
        self.dl = []
        self.timer_stop = None
        self.last_timer_stop = None
        self.recent_tokenin = None
        self.delay_list = []
        _log.info("I am {} actor.".format(self.name))
        self.setup()

    #Read the file of delays and get the delay mesurements
    def setup(self):
        self.timer = calvinsys.open(self, "sys.timer.once")
        self.use('calvinsys.native.python-time', shorthand='time')
        self.time = self['time']

    #@stateguard(lambda self: self.ToWrite and not self.ToRead)
    @condition(['token'], [])
    def token_available(self, token):
        _log.info("{}: Token arrives at tick: {} ".format(self.name, tick))
        self.timer_stop = self.time.timestamp()
        self.recent_tokenin = self.timer_stop
        self.delay = token[1][0]
        if len(self.delay_list) > 0:
            _log.info("{}: Still holding {} tokens in the list".format(self.name, len(self.delay_list)))
            duration = self.timer_stop - self.last_timer_stop
            for x in self.delay_list:
                x['delay'] -= duration

        self.delay_list.append({'token': token, 'delay': self.delay})
        self.delay_list = sorted(self.delay_list, key=lambda k: k['delay'])
        
        if not calvinsys.can_write(self.timer):
            calvinsys.read(self.timer)
            calvinsys.close(self.timer)
        self.last_timer_stop = self.time.timestamp()
        calvinsys.write(self.timer, self.delay)

    @stateguard(lambda self: calvinsys.can_read(self.timer))
    @condition([], ['token'])
    def passthrough(self):
        _log.warning('{}: passthrough'.format(self.name))
        calvinsys.read(self.timer)
        item = self.delay_list.pop(0)
        self.timer_stop = self.time.timestamp()
        if len(self.delay_list) > 0:
            duration = self.timer_stop - self.last_timer_stop
            for x in self.delay_list:
                x['delay'] -= duration
            self.delay = self.delay_list[0]['delay']
            if self.delay < 0:
                self.delay = 0
            calvinsys.write(self.timer, self.delay)
        self.last_timer_stop = self.time.timestamp()
        return (item['token'], )

    action_priority = (passthrough, token_available, )
    requires = ['sys.timer.once']

