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
percentage_pedestrians_running = 0.0      # how many pedestrians will run
percentage_pedestrians_crossing = 0.0     # how many pedestrians will walk through the road

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
        self.other_actors = []
        logger.debug_s(f"ego: {ego_vehicles}")
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
        logger.debug_s(f"Spawning and attaching ai controllers to pedestrians")
        pedestrians_location = [actor.get_transform() for actor in self.other_actors]
        pedestrians_amount = len(self.other_actors)
        logger.debug_s(f"Pedestrian amount: {pedestrians_amount}")
        batch = []
        walker_controller_bp = CarlaDataProvider.get_world().get_blueprint_library().find('controller.ai.walker')
        for i in range(pedestrians_amount):
            batch.append(carlaSpawnActor(walker_controller_bp, self.other_actors[i].get_transform(), self.other_actors[i].id))
        self.ai_controllers = batch
        CarlaDataProvider.handle_actor_batch(batch, True)

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