from __future__ import print_function, annotations
from typing import List, Union

import os
import py_trees
from py_trees.behaviour import Behaviour

from srunner.scenariomanager.scenarioatomics.atomic_behaviors import KeepVelocity
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance
from srunner.scenarios.object_crash_vehicle import DynamicObjectCrossing

from customs.configs.config import OUT_DIR
from customs.behaviors.horn_behavior import HornBehavior

class PedestrianCyclistCrossing(DynamicObjectCrossing):
    """
    Base of pedestrian crossing scenario
    """
    custom_name = None
    custom_speed = None
    adversary_type = False

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False,
                 debug_mode=False, 
                 criteria_enable=False,
                 name: str="PedestrianCyclistCrossing",
                 timeout=60):
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         name=name if self.custom_name is None else name,
                         randomize=randomize, 
                         debug_mode=debug_mode, 
                         criteria_enable=criteria_enable, 
                         spawn_blocker=False,
                         adversary_type=self.adversary_type,
                         timeout=timeout)
    

    def _create_behavior(self):
        def find_behavior_by_name(root_behavior: Behaviour, name: str) -> Union[Behaviour, None]:
            for behavior in root_behavior.iterate():
                if behavior.name == name:
                    return behavior
            return None
        
        def find_behavior_by_class(root_behavior: Behaviour, classtype) -> Union[Behaviour , None]:
            for behavior in root_behavior.iterate():
                if isinstance(behavior, classtype):
                    return behavior
            return None

        def change_crossing_speed(behavior: Behaviour):
            if self.custom_speed is None:
                return behavior 

            # find keep velocity
            target_node = find_behavior_by_name(behavior, "keep velocity")
            if target_node is not None:
                # change velocity to custom speed
                keep_velocity = find_behavior_by_class(target_node, KeepVelocity)
                if keep_velocity is not None:
                    keep_velocity._target_velocity = self.custom_speed

                # make the speed consistent for the whole crossing
                # drive_distance = find_behavior_by_class(target_node, DriveDistance)
                # if drive_distance is not None:
                #     drive_distance._target_distance *= 2

            return behavior

        def insert_horn_behavior(behavior: Behaviour):
            out_horn_behavior = find_behavior_by_name(behavior, "keep velocity")
            out_horn_behavior_other = find_behavior_by_name(behavior, "keep velocity other")
            parent = out_horn_behavior.parent

            horn_behavior = HornBehavior(self.ego_vehicles[0],
                                         self.other_actors[0], 
                                         name="Pedestrian horn behavior", 
                                         out_horn_behavior=out_horn_behavior)
            horn_behavior_other = HornBehavior(self.ego_vehicles[0],
                                         self.other_actors[0], 
                                         name="Pedestrian horn behavior", 
                                         out_horn_behavior=out_horn_behavior_other)
            # replace the existing behavior with the horn behavior
            parent.replace_child(out_horn_behavior, horn_behavior)
            parent.replace_child(out_horn_behavior_other, horn_behavior_other)
            return behavior

        behavior = super()._create_behavior()

        if self.custom_speed is not None:
            behavior = change_crossing_speed(behavior)

        behavior = insert_horn_behavior(behavior)
        return behavior

class PedestrianCrossing(PedestrianCyclistCrossing):
    custom_name = "PedestrianCrossing"
    adversary_type = False

class PedestrianWalkCrossing(PedestrianCrossing):
    custom_name = "PedestrianWalkCrossing"
    custom_speed = 0.7

class CyclistCrossing(PedestrianCyclistCrossing):
    custom_name = "CyclistCrossing"
    adversary_type = True

class CyclistSlowCrossing(CyclistCrossing):
    custom_name = "CyclistSlowCrossing"
    custom_speed = 0.7
