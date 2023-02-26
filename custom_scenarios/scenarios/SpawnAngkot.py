#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import carla
import py_trees

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorTransformSetter
from srunner.scenarios.background_activity import BackgroundActivity
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToLocationAlongRoute, DriveDistance

class SpawnAngkot(BackgroundActivity):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self.config = config
        self.debug = debug_mode
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location

        self.timeout = timeout  # Timeout of scenario in seconds

        super(BackgroundActivity, self).__init__("BackgroundActivity",
                                                 ego_vehicles,
                                                 config,
                                                 world,
                                                 debug_mode,
                                                 terminate_on_failure=True,
                                                 criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        def get_distance_from_wp(ego_vehicle, waypoint):
            ego_location = CarlaDataProvider.get_location(ego_vehicle)
            if ego_location is None:
                return False
            return waypoint.transform.location.distance(ego_location)
        
        distance_threshold = 2
        while True:
            distance_from_wp = get_distance_from_wp(self.ego_vehicles[0], self._reference_waypoint)
            if distance_from_wp and distance_from_wp <= distance_threshold:
                break
                
        new_actors = CarlaDataProvider.request_new_batch_actors('angkot',
                                                                50,
                                                                carla.Transform(),
                                                                autopilot=True,
                                                                random_location=True,
                                                                rolename='background')

        if new_actors is None:
            raise Exception("Error: Unable to add the background activity, all spawn points were occupied")

        print(f"Angkot spawned: {len(new_actors)}")
        self.other_actors.extend(new_actors)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        root = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="SpawnAngkot")
        
        others_behavior = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="SpawnAngkot")
        
        root.add_child(others_behavior)
        for idx, other in enumerate(self.other_actors):
            location = CarlaDataProvider.get_location(other)
            others_behavior.add_child(ActorTransformSetter(other, location,
                                                         name=f'TransformSetterActor_{idx}'))
            
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
