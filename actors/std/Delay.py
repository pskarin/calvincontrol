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

class Delay(Actor):
    """
    After first token, pass on token once every 'delay' seconds.
    Input :
        token: anything
    Outputs:
        token: anything
    """

    @manage(['timer', 'delay', 'started', 'path'])
    def init(self, path):
        self.delay = 0
        self.timer = calvinsys.open(self, "sys.timer.repeating")
        self.started = False
        self.path = path
        self.seq = []
        self.dl = []
        self.counter = 0
        self.packetloss = False
        self.setup()

    def setup(self):
        f = open(self.path, 'r')
        # Read the timestamp,delay and seq number from the file
        for line in f.readlines():
            s = line.split("\t")[0]
            self.seq.append(s)
            d = line.split("\t")[1]
            self.dl.append(d)

        f.close()

    @stateguard(lambda self: not self.started and calvinsys.can_write(self.timer))
    @condition(['token', 'tick'], ['token']) #have a pointer point to the current seq number
    def start_timer(self, token, tick):
        self.started = True
        sq = self.seq[self.counter]
        if sq == tick:
            self.delay = self.dl[self.counter]/2
            self.counter += 1
            self.packetloss = False
        else:
            self.delay = 0
            self.packetloss = True

        calvinsys.write(self.timer, self.delay)
        return (token, )

    @stateguard(lambda self: calvinsys.can_read(self.timer) and not self.packetloss)
    @condition(['token'], ['token'])
    def passthrough(self, token):
        calvinsys.read(self.timer)
        return (token, )

    @stateguard(lambda self: calvinsys.can_read(self.timer) and self.packetloss)
    @condition(['token'], [])
    def droptocken(self):
        calvinsys.read(self.timer)

    action_priority = (start_timer, passthrough, droptocken)
    requires = ['sys.timer.repeating']


    # test_kwargs = {'delay': 20}
    # test_calvinsys = {'sys.timer.repeating': {'read': ["d", "u", "m", "m", "y"],
    #                                           'write': [20]}}
    # test_set = [
    #     {
    #         'inports': {'token': ["a", "b", 1]},
    #         'outports': {'token': ["a", "b", 1]}
    #     }
    # ]
