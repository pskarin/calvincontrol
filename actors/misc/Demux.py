from calvin.actor.actor import Actor, condition

class Demux(Actor):
    """
    Collect 3 inputs
    Inputs:
      arr : token array [pos, ang, ref]
    Outputs:
      pos : position
      ang : angle
      ref : ref
    """

    def init(self):
        pass

    @condition(['arr'], ['pos', 'ang', 'ref'])
    def distribute(self, arr):
        return (arr[0], arr[1], arr[2])

    action_priority = (distribute,)
