#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""
import carla

import logging
from custom_scenarios.helpers.blueprints import create_blueprints_by_attribute
from custom_scenarios.scenarios.SpawnActor import SpawnActor, SpawnActorOnTrigger
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

logger = logging.getLogger(__name__)
total_amount = 20
pedestrian_modelnames = ["walker.*"]
pedestrian_ai_controller = ["controller.ai.walker"]
carlaSpawnActor = carla.command.SpawnActor


class SpawnPedestrian(SpawnActor):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        """
        Setup all relevant parameters and create scenario
        """
        super(SpawnPedestrian, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_names=pedestrian_modelnames,
                                            total_amount=total_amount)
        self._attach_ai_controller()
    
    def _attach_ai_controller(self):
        pedestrians_location = [actor.get_transform() for actor in self.other_actors]
        pedestrians_amount = len(self.other_actors)
        self.ai_controllers = CarlaDataProvider.request_new_batch_actors(pedestrian_ai_controller[0],
                                                                         pedestrians_amount,
                                                                         pedestrians_location,
                                                                         random_location=False,
                                                                         rolename="ai_walker")

class SpawnPedestrianOnTrigger(SpawnActorOnTrigger):
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        super(SpawnPedestrianOnTrigger, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_names=pedestrian_modelnames,
                                            total_amount=total_amount)