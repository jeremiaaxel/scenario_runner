import py_trees
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import AtomicBehavior


class ToggleWalkerController(AtomicBehavior):
    def __init__(self, ai_controller, start=True, name="ToggleWalkerController"):
        super().__init__(name, ai_controller)
        self.logger.debug("%s.__init__()" % (self.__class__.__name__))
        self.start = start

    def update(self):
        if self.start:
            self._actor.start()
        else:
            self._actor.stop()
        
        new_status = py_trees.common.Status.SUCCESS

        self.logger.debug("%s.update()[%s->%s]" % (self.__class__.__name__, self.status, new_status))
        return new_status
