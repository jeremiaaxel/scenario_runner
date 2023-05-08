from __future__ import print_function

import os
import math
import carla
import py_trees

from customs.behaviors.horn_behavior import HornBehavior
from customs.configs.config import OUT_DIR
from customs.triggers.horn_trigger import InHornDistanceTrigger

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                      ActorDestroy)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_location_in_distance_from_wp

class ObstructingVehicle(BasicScenario):
    """
    This class holds everything required for a simple object crash
    without prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a stationary vehicle.

    This is a single ego vehicle scenario
    """
    model_name = "vehicle.carlamotors.firetruck"
    _horn_distance = 15

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True,
                 model_name=model_name,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        # ego vehicle parameters
        self._ego_vehicle_distance_driven = 40
        # other vehicle parameters
        self._other_actor_target_velocity = 10
        # Timeout of scenario in seconds
        self.timeout = timeout
        self.model_name = model_name

        super(__class__, self).__init__(self.__class__.__name__,
                                                       ego_vehicles,
                                                       config,
                                                       world,
                                                       debug_mode,
                                                       criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """
        Custom initialization
        """
        _start_distance = 40
        lane_width = self._reference_waypoint.lane_width
        location, _ = get_location_in_distance_from_wp(self._reference_waypoint, _start_distance)
        waypoint = self._wmap.get_waypoint(location)
        offset = {"orientation": 270, "position": 90, "z": 0.4, "k": 0.2}
        position_yaw = waypoint.transform.rotation.yaw + offset['position']
        orientation_yaw = waypoint.transform.rotation.yaw + offset['orientation']
        offset_location = carla.Location(
            offset['k'] * lane_width * math.cos(math.radians(position_yaw)),
            offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
        location += offset_location
        location.z += offset['z']
        self.transform = carla.Transform(location, carla.Rotation(yaw=orientation_yaw))
        vehicle = CarlaDataProvider.request_new_actor(self.model_name, self.transform)
        vehicle.set_simulate_physics(True)
        vehicle.set_autopilot(False)
        self.other_actors.append(vehicle)

    def _create_behavior(self):
        """
        The vehicle was parked
        after horned, 15 seconds, the vehicle starts to operate normally
        """
        lane_width = self.ego_vehicles[0].get_world().get_map().get_waypoint(
            self.ego_vehicles[0].get_location()).lane_width
        lane_width = lane_width + (1.25 * lane_width)

        # leaf nodes
        actor_stand = TimeOut(15)
        actor_removed = ActorDestroy(self.other_actors[0])
        end_condition = DriveDistance(self.ego_vehicles[0], self._ego_vehicle_distance_driven)
        in_horn_trigger = InHornDistanceTrigger(self.ego_vehicles[0],
                                                    self.other_actors[0],
                                                    trigger_distance=self._horn_distance,
                                                    name=f"In horn distance {self.other_actors[0].id}")
        horn_behavior = HornBehavior(self.ego_vehicles[0], self.other_actors[0],
                                     "Obstructing vehicle on horn")

        # non leaf nodes
        root = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        scenario_sequence = py_trees.composites.Sequence()

        # building tree
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], self.transform))
        scenario_sequence.add_child(in_horn_trigger) 
        scenario_sequence.add_child(actor_stand)
        scenario_sequence.add_child(horn_behavior) 
        scenario_sequence.add_child(actor_removed)
        scenario_sequence.add_child(end_condition)
        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        collision_criterion = CollisionTest(self.ego_vehicles[0])
        criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

