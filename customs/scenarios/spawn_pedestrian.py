#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""
import random
from typing import List
import carla

import logging
from customs.helpers.blueprints import freeze_pedestrians, generate_walker_spawn_points, get_actor_blueprints, hide_actors
from customs.scenarios.spawn_actor import SpawnActor, SpawnActorOnTrigger
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

logger = logging.getLogger(__name__)
total_amount = 200
pedestrian_modelnames = ["walker.*"]
pedestrian_ai_controller = ["controller.ai.walker"]
carlaSpawnActor = carla.command.SpawnActor
percentage_pedestrians_running = 0.5      # how many pedestrians will run
percentage_pedestrians_crossing = 1.0     # how many pedestrians will walk through the road


class SpawnPedestrian(SpawnActor):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=True, debug_mode=False, timeout=35 * 60, criteria_enable=False, spawn_points: list=None):
        """
        Setup all relevant parameters and create scenario
        """
        super().__init__(world,
                        ego_vehicles,
                        config,
                        randomize,
                        spawn_points=spawn_points,
                        debug_mode=debug_mode,
                        timeout=timeout,
                        criteria_enable=criteria_enable,
                        model_names=pedestrian_modelnames,
                        amounts=[total_amount])
    
    def _spawn_walkers(self):
        world = CarlaDataProvider.get_world()
        client = CarlaDataProvider.get_client()

        world.set_pedestrians_cross_factor(percentage_pedestrians_crossing)

        for modelname, amount in zip(self.model_names, self.amounts):
            if self.randomize or self.spawn_points is None:
                self.spawn_points = generate_walker_spawn_points(world, amount)
            number_of_spawn_points = len(self.spawn_points)
            blueprints = get_actor_blueprints(world, modelname, generation='all')

            if amount > number_of_spawn_points:
                msg = 'requested %d pedestrians, but could only find %d spawn points'
                logging.warning(msg, amount, number_of_spawn_points)

            batch = []
            walker_speed = []
            for spawn_point in self.spawn_points:
                walker_bp = random.choice(blueprints)
                # set as not invincible
                if walker_bp.has_attribute('is_invincible'):
                    walker_bp.set_attribute('is_invincible', 'false')
                # set the max speed
                speed = 0.0
                if walker_bp.has_attribute('speed'):
                    speed = walker_bp.get_attribute('speed').recommended_values[1 if random.random() >= percentage_pedestrians_running else 2]
                else:
                    print("Walker has no speed")
                walker_speed.append(speed)
                walker_bp.set_attribute('speed', speed)
                batch.append(carlaSpawnActor(walker_bp, spawn_point))

        results = client.apply_batch_sync(batch, True)
        walker_speed2 = []
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walker_speed2.append(walker_speed[i])
        self.walker_speed = walker_speed2

        walkers = world.get_actors([result.actor_id for result in results])
        self.other_actors.extend(walkers)
        CarlaDataProvider.insert_spawned_actors(walkers)

    def _spawn_actors(self, config):
        self._spawn_walkers()

    def _post_initialize_actors(self, config):
        self._attach_ai_controller()

    def _attach_ai_controller(self):
        logger.debug_s(f"Spawning and attaching ai controllers to pedestrians")

        world = CarlaDataProvider.get_world()
        client = CarlaDataProvider.get_client()
        
        pedestrians_amount = len(self.other_actors)
        logger.debug_s(f"Pedestrian amount: {pedestrians_amount}")

        batch = []
        walker_controller_bp = world.get_blueprint_library().find(pedestrian_ai_controller[0])
        for i in range(pedestrians_amount):
            batch.append(carlaSpawnActor(walker_controller_bp, self.other_actors[i].get_transform(), self.other_actors[i].id))
        results = client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
        ai_controllers = world.get_actors([result.actor_id for result in results])
        self.ai_controllers = ai_controllers

        CarlaDataProvider.insert_spawned_actors(ai_controllers)

        for ai_controller in self.ai_controllers:
            target_location = world.get_random_location_from_navigation()
            ai_controller.start()
            ai_controller.go_to_location(target_location)

    def remove_ai_controllers(self):
        if self.ai_controllers is None:
            return
        
        logger.info(f"Stopping {len(self.ai_controllers)} AI controllers")
        for i, _ in enumerate(self.ai_controllers):
            if self.ai_controllers[i] is not None:
                self.ai_controllers[i].stop()
                if CarlaDataProvider.actor_id_exists(self.ai_controllers[i].id):
                    CarlaDataProvider.remove_actor_by_id(self.ai_controllers[i].id)
        self.ai_controllers = []

    def remove_all_actors(self):
        self.remove_ai_controllers()
        super().remove_all_actors()

class SpawnPedestrianOnTrigger(SpawnPedestrian, SpawnActorOnTrigger):
    def _post_initialize_actors(self, config):
        super()._post_initialize_actors(config)
        self._move_actors_in_trigger_location()
        freeze_pedestrians(self.ai_controllers)
        # put all actors underground
        hide_actors(self.other_actors,
                    underground_z=self.underground_z, freeze=True)