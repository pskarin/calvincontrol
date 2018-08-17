from calvin.actor.actor import Actor, manage, condition, stateguard, calvinsys

class Delay(Actor):

    @manage(['timers', 'delay', 'path'])
    def init(self):
        self.delay = 0
        self.path = "~/calvincontrol/data.txt"
        self.seq = []
        self.dl = []
        self.counter = 0
        self.token = 0
        self.tick = 0
        self.loss = False
        self.setup()

    def setup(self):
        f = open(self.path, 'r')
        # Read the timestamp,delay and seq number from the file
        for line in f.readlines():
            s = line.split(",")[0]
            self.seq.append(s)
            d = line.split(",")[1]
            self.dl.append(d)

        f.close()

    def new_timer(self):
        sq = self.seq[self.counter]
        if sq == self.tick:
            self.delay = self.dl[self.counter]/2000.
            self.counter += 1
            self.loss = False
            print self.delay
        else:
            self.delay = 0
            self.loss = True
            print "Packet Lost"

        timer = calvinsys.open(self, "sys.timer.once", period=self.delay)
        return timer


        #return (self.token, )

    @condition(['token', 'tick'])
    def token_available(self, token, tick):
        self.tick = tick
        self.timers.append({'token': token, 'timer': self.new_timer()})

    @stateguard(lambda self: len(self.timers) > 0 and calvinsys.can_read(self.timers[0]['timer']))
    @condition([], ['token'])
    def timeout(self):
        item = self.timers.pop(0)
        calvinsys.read(item['timer'])
        calvinsys.close(item['timer'])

        return (item['token'], )

        
    action_priority = (timeout, token_available)
    requires = ['sys.timer.once']

