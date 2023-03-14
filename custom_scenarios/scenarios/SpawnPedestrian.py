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
    
    # def _attach_ai_controller(self):
    #     for pedestrian in self.other_actors:
    #         carlaSpawnActor(pedestrian_ai_controller, pedestrian.get_transform(), pedestrian).then(lambda aiControl: aiControl.start())

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