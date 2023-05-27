from __future__ import print_function

import os
import math
from typing import Literal
import carla
import py_trees
import logging
import random

from customs.behaviors.horn_behavior import HornBehavior
from customs.behaviors.toggle_walker_controller import ToggleWalkerController
from customs.helpers.blueprints import freeze_pedestrians, freeze_vehicle, generate_walker_spawn_points, get_actor_blueprints, hide_actor, hide_actors
from customs.helpers.config import OUT_DIR
from customs.triggers.horn_trigger import InHornDistanceTrigger

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                      ActorDestroy, ChangeAutoPilot)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_location_in_distance_from_wp


logger = logging.getLogger(__name__)
carlaSpawnActor = carla.command.SpawnActor

class ObstructingActor(BasicScenario):
    """
    This class holds everything required for a simple object crash
    without prior vehicle action involving a vehicle and a cyclist.
    The ego vehicle is passing through a road and encounters
    a stationary vehicle.

    This is a single ego vehicle scenario
    """
    model_name = "vehicle.carlamotors.firetruck"
    _horn_distance = 15
    underground_z = 500

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True,
                 model_name=model_name,
                 trigger: Literal['horn', 'timer']='horn',
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
        self.trigger = trigger
        self.model_name = model_name
        self.ai_controllers = [] # automatically set on child class

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
        _start_distance = 20
        lane_width = self._reference_waypoint.lane_width
        location, _ = get_location_in_distance_from_wp(self._reference_waypoint, _start_distance)
        waypoint = self._wmap.get_waypoint(location)
        offset = {"orientation": 270, "position": 90, "z": 0.6, "k": 0.2}
        position_yaw = waypoint.transform.rotation.yaw + offset['position']
        orientation_yaw = waypoint.transform.rotation.yaw + offset['orientation']
        offset_location = carla.Location(
            offset['k'] * lane_width * math.cos(math.radians(position_yaw)),
            offset['k'] * lane_width * math.sin(math.radians(position_yaw)))
        location += offset_location
        location.z += offset['z']
        self.transform = carla.Transform(location, carla.Rotation(yaw=orientation_yaw))
        actor = CarlaDataProvider.request_new_actor(self.model_name, self.transform)
        actor.set_simulate_physics(True)
        self.other_actors.append(actor)
        
        # put actor underground
        # self.hide_actors()
        # location = actor.get_location()
        # uground_location = carla.Location(location.x, location.y, location.z - 100)
        # actor.set_location(uground_location)
        # actor.set_simulate_physics(False)
        # if isinstance(actor, carla.Vehicle):
        #     actor.set_autopilot(False)
        # hide_actor(actor, freeze=True)
        
    def hide_actors(self):
        for other_actor in self.other_actors:
            location = other_actor.get_location()
            uground_location = carla.Location(location.x,
                                              location.y,
                                              location.z - self.underground_z)
            # SOMEHOW THIS CAUSES SEGFAULT
            # other_actor.set_location(uground_location)
            other_actor.set_simulate_physics(enabled=False)

            if isinstance(other_actor, carla.Vehicle):
                freeze_vehicle(other_actor)

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
                                                    self.ai_controllers[0] if isinstance(self.other_actors[0], carla.WalkerAIController) else self.other_actors[0],
                                                    trigger_distance=self._horn_distance,
                                                    name=f"In horn distance {self.other_actors[0].id}")
        horn_behavior = HornBehavior(self.ego_vehicles[0], 
                                     self.ai_controllers[0] if isinstance(self.other_actors[0], carla.WalkerAIController) else self.other_actors[0],
                                    "Obstructing actor on horn",
                                    in_horn_meta=py_trees.meta.success_is_running,
                                    out_horn_meta=py_trees.meta.success_is_running)

        # non leaf nodes
        root = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        scenario_sequence = py_trees.composites.Sequence()

        # building tree
        root.add_child(scenario_sequence)
        scenario_sequence.add_child(ActorTransformSetter(self.other_actors[0], 
                                                         self.transform, 
                                                         physics=True))
        if self.trigger == 'horn':
            scenario_sequence.add_child(in_horn_trigger) 
        scenario_sequence.add_child(actor_stand)
        if isinstance(self.other_actors[0], carla.Vehicle):
            scenario_sequence.add_child(ChangeAutoPilot(self.other_actors[0], True))
        elif isinstance(self.other_actors[0], carla.Walker):
            scenario_sequence.add_child(ToggleWalkerController(self.ai_controllers[0], True))
        scenario_sequence.add_child(horn_behavior) 
        scenario_sequence.add_child(actor_removed)
        scenario_sequence.add_child(end_condition)

        # py_trees.display.render_dot_tree(root, name=os.path.join(OUT_DIR, __class__.__name__))
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


class ObstructingPedestrian(ObstructingActor):
    percentage_pedestrians_running = 30.0      # how many pedestrians will run
    percentage_pedestrians_crossing = 50.0     # how many pedestrians will walk through the road
    ai_controller_model = "controller.ai.walker"
    
    def _spawn_walkers(self):
        world = CarlaDataProvider.get_world()
        client = CarlaDataProvider.get_client()

        world.set_pedestrians_cross_factor(self.percentage_pedestrians_crossing)

        total_amount = self.total_amount
        if self.randomize or self.spawn_points is None:
            self.spawn_points = generate_walker_spawn_points(world, total_amount)
        number_of_spawn_points = len(self.spawn_points)
        blueprints = get_actor_blueprints(world, self.model_name, generation='all')

        if total_amount > number_of_spawn_points:
            msg = 'requested %d pedestrians, but could only find %d spawn points'
            logging.warning(msg, total_amount, number_of_spawn_points)
            total_amount = number_of_spawn_points

        batch = []
        walkers_list = []
        walker_speed = []
        for spawn_point in self.spawn_points:
            walker_bp = random.choice(blueprints)
            # set as not invincible
            if walker_bp.has_attribute('is_invincible'):
                walker_bp.set_attribute('is_invincible', 'false')
            # set the max speed
            if walker_bp.has_attribute('speed'):
                if random.random() > self.percentage_pedestrians_running:
                    # walking
                    walker_speed.append(walker_bp.get_attribute('speed').recommended_values[1])
                else:
                    # running
                    walker_speed.append(walker_bp.get_attribute('speed').recommended_values[2])
            else:
                print("Walker has no speed")
                walker_speed.append(0.0)
            batch.append(carlaSpawnActor(walker_bp, spawn_point))

        results = client.apply_batch_sync(batch, True)
        # walker_speed2 = []
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
        #     else:
        #         walkers_list.append({"id": results[i].actor_id})
        #         walker_speed2.append(walker_speed[i])
        # walker_speed = walker_speed2

        walkers = world.get_actors([result.actor_id for result in results])
        self.other_actors.extend(walkers)
        CarlaDataProvider.insert_spawned_actors(walkers)

    def _attach_ai_controller(self):
        logger.debug_s(f"Spawning and attaching ai controllers to pedestrians")

        world = CarlaDataProvider.get_world()
        client = CarlaDataProvider.get_client()
        
        pedestrians_amount = len(self.other_actors)
        logger.debug_s(f"Pedestrian amount: {pedestrians_amount}")

        batch = []
        walker_controller_bp = world.get_blueprint_library().find(self.ai_controller_model)
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
    
    def _initialize_actors(self, config):
        super()._initialize_actors(config)
        # self._spawn_walkers()
        self._attach_ai_controller()
        freeze_pedestrians(self.ai_controllers)

    def remove_all_actors(self):
        self.remove_ai_controllers()
        super().remove_all_actors()
        

class ObstructingVehicleHorn(ObstructingActor):
    model_name = "vehicle.tesla.model3"
    trigger = 'horn'

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True, 
                 model_name=model_name, 
                 timeout=60):
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         randomize, 
                         debug_mode, 
                         criteria_enable, 
                         model_name, trigger=self.trigger, timeout=timeout)

class ObstructingVehicleTimer(ObstructingActor):
    model_name = "vehicle.ford.crown"
    trigger = 'timer'

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True, 
                 model_name=model_name, 
                 timeout=60):
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         randomize, 
                         debug_mode, 
                         criteria_enable, 
                         model_name, trigger=self.trigger, timeout=timeout)

class ObstructingPedestrianHorn(ObstructingPedestrian):
    model_name = "walker.*"
    trigger = 'horn'

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True, 
                 model_name=model_name, 
                 timeout=60):
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         randomize, 
                         debug_mode, 
                         criteria_enable, 
                         model_name, trigger=self.trigger, timeout=timeout)

class ObstructingPedestrianTimer(ObstructingPedestrian):
    model_name = "walker.*"
    trigger = 'timer'

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, 
                 randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True, 
                 model_name=model_name, 
                 timeout=60):
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         randomize, 
                         debug_mode, 
                         criteria_enable, 
                         model_name, trigger=self.trigger, timeout=timeout)