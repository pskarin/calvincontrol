from calvin.actor.actor import Actor, condition

class Mux(Actor):
    """
    Collect 3 inputs
    Inputs:
      pos : position
      ang : angle
      ref : ref
    Outputs:
      arr : resulting token array
    """

    def init(self):
        pass

    @condition(['pos', 'ang', 'ref'], ['arr'])
    def collect(self, pos, ang, ref):
        return ([pos, ang, ref], )

    action_priority = (collect,)