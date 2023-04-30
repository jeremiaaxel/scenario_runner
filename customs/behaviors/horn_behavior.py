import carla
import py_trees

from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot, StopVehicle
from customs.triggers.horn_trigger import InHornDistanceTrigger

class HornBehavior(py_trees.composites.Parallel):
    def __init__(self, 
                 reference_actor,
                 actor, 
                 name="HornBehavior", 
                 policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE,
                 horn_distance=20,
                 in_horn_behavior=None,
                 out_horn_behavior=None,
                 swap_behavior=False):
        super().__init__(name, policy=policy)
        self._actor = actor
        self._reference_actor = reference_actor
        self._horn_distance = horn_distance
        self.swap_behavior = swap_behavior

        if out_horn_behavior is None:
            out_horn_behavior = self.default_out_behavior()

        if in_horn_behavior is None:
            in_horn_behavior = self.default_in_behavior()

        if swap_behavior:
            in_horn_behavior, out_horn_behavior = out_horn_behavior, in_horn_behavior

        self.attach_to_out_horn_trigger(out_horn_behavior)
        self.attach_to_in_horn_trigger(in_horn_behavior)

    def attach_to_in_horn_trigger(self, in_horn_behavior) -> None:
        in_horn_behavior_complete = py_trees.meta.success_is_running(py_trees.composites.Sequence)(name="In horn distance behavior")
        in_horn_behavior_complete.add_child(InHornDistanceTrigger(self._reference_actor,
                                                    self._actor,
                                                    trigger_distance=self._horn_distance,
                                                    name=f"In horn distance {self._actor.id}"))
        in_horn_behavior_complete.add_child(in_horn_behavior)
        self.add_child(in_horn_behavior_complete)

    def attach_to_out_horn_trigger(self, out_horn_behavior) -> None:
        out_horn_behavior_complete = py_trees.meta.success_is_running(py_trees.composites.Sequence)(name="Not in horn distance behavior")
        out_horn_behavior_complete.add_child(out_horn_behavior)
        self.add_child(out_horn_behavior_complete)

    def default_in_behavior(self):
        """
        if horned at: 
          vehicle: stop on, autopilot off
          walker: stop on
        """
        in_horn_behavior = py_trees.composites.Sequence()
        in_horn_behavior.add_child(StopVehicle(self._actor, 1, name=f"Stop on {self._actor.id}"))
        if isinstance(self._actor, carla.Vehicle):
            in_horn_behavior.add_child(ChangeAutoPilot(self._actor, False, name=f"Autopilot off {self._actor.id}"))
        return in_horn_behavior
    
    def default_out_behavior(self):
        """
        if not horned at:
          vehicle:stop off, autopilot on
          walker:stop off
        """
        # this is automatically success, so change to running so that in horn can prevail if it is true (success)
        out_horn_behavior = py_trees.composites.Sequence()
        out_horn_behavior.add_child(StopVehicle(self._actor, 0, name=f"Stop off {self._actor.id}"))
        if isinstance(self._actor, carla.Vehicle):
            out_horn_behavior.add_child(ChangeAutoPilot(self._actor, True, name=f"Autopilot on {self._actor.id}"))
        return out_horn_behavior
    