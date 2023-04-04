
import operator
import py_trees

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import AtomicCondition, InTriggerDistanceToVehicle, WaitForBlackboardVariable

class InHornDistanceTrigger(AtomicCondition):
    """
    Trigger other vehicles in distance if horn is activated
    Implemented using InTriggerDistanceToVehicle and WaitForBlackboardVariable
    """
    def __init__(self, actor, other_actor, trigger_distance = 5, name="InHornDistanceTrigger"):
        super().__init__(name)
        self._actor = actor
        self._other_actor = other_actor
        self._trigger_distance = trigger_distance
        self._in_trigger_distance_to_vehicle = InTriggerDistanceToVehicle(self._actor, 
                                                                          self._other_actor,
                                                                          self._trigger_distance,
                                                                          comparison_operator=operator.le)
        self._wait_for_blackboard_variable = WaitForBlackboardVariable("is_ego_vehicle_horn",
                                                                       True,
                                                                       False)

    def update(self):
        new_status = py_trees.common.Status.RUNNING

        # status is SUCCESS if ego is horn and is in distance
        is_ego_horn = self._wait_for_blackboard_variable.update()
        if is_ego_horn != py_trees.common.Status.SUCCESS:
            return new_status
        
        in_distance = self._in_trigger_distance_to_vehicle.update()
        if in_distance == py_trees.common.Status.SUCCESS:
            new_status = py_trees.common.Status.SUCCESS

        return new_status