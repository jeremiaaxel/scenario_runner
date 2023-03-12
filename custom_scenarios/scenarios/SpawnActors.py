#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import carla
import py_trees
import logging

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorTransformSetter
from srunner.scenarios.background_activity import BackgroundActivity
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToLocationAlongRoute, DriveDistance

logger = logging.getLogger(__name__)

class SpawnActors(BackgroundActivity):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    amount = 50

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False, model_name='vehicle.*'):
        """
        Setup all relevant parameters and create scenario
        """
        logger.debug_s("Initializing scenario")
        self._wmap = CarlaDataProvider.get_map()
        self.config = config
        self.debug = debug_mode
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        logger.debug_s(self._trigger_location)

        self.timeout = timeout  # Timeout of scenario in seconds

        self.model_name = model_name

        super(SpawnActors, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            debug_mode=debug_mode,
                                            criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        destroy_distance = 3
        logger.debug_s("Initializing actor")
        new_actors = CarlaDataProvider.request_new_batch_actors(self.model_name,
                                                                self.amount,
                                                                carla.Transform(),
                                                                autopilot=True,
                                                                random_location=True,
                                                                rolename='background')

        if new_actors is None:
            raise Exception("Error: Unable to add the background activity, all spawn points were occupied")

        # avoid spawning on the ego vehicle location
        for actor in new_actors:
            if actor.get_location().distance(self._trigger_location) < destroy_distance:
                logger.debug_s(f"{actor.id} is too close ma man")
                CarlaDataProvider.remove_actor_by_id(actor.id)

        print(f"{self.model_name} spawned: {len(new_actors)}")
        self.other_actors.extend(new_actors)

    def _create_behavior(self):
        """
        Basic behavior do nothing, i.e. Idle
        """
        logger.debug_s("Creating behavior")
        pass

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        logger.debug_s("Creating test criteria")

        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])

        criteria.append(collision_criterion)
        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        logger.debug_s("Deleting")

        self.remove_all_actors()
