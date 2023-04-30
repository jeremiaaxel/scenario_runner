#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import py_trees
from py_trees.common import ParallelPolicy
from py_trees.composites import Sequence, Parallel

import os
import carla
import logging
from customs.behaviors.horn_behavior import HornBehavior

from customs.configs.config import OUT_DIR
from customs.triggers.horn_trigger import InHornDistanceTrigger
from multisensors.utils.manual_control_global_funcs import get_actor_display_name

from srunner.scenarios.background_activity import BackgroundActivity
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot, ActorTransformSetter, Idle, KeepLongitudinalGap, KeepVelocity, ActorDestroy, HandBrakeVehicle, StopVehicle
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance, InTimeToArrivalToVehicle, InTriggerDistanceToLocationAlongRoute

logger = logging.getLogger(__name__)

class SpawnActor(BackgroundActivity):
    """
    Spawn batch actor(s) with multiple model filter
    """
    _dist_to_trigger = 20
    _horn_distance = 20
    _time_to_reach = 1

    underground_z = 500
    _other_actor_target_velocity = 5
    _ego_vehicle_distance_driven = -1 # set value <= 0 to make the scenario endless
    do_print = True
    _ego_route = None

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False, model_names=['vehicle.*'], total_amount=50):
        """
        Setup all relevant parameters and create scenario
        """
        logger.debug_s("Initializing scenario")
        self.other_actors = []
        self._wmap = CarlaDataProvider.get_map()
        self.config = config
        self.debug = debug_mode
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        logger.debug_s(f"Trigger location: {self._trigger_location}")

        self.timeout = timeout  # Timeout of scenario in seconds

        self.model_names = model_names
        self.total_amount = total_amount

        super(SpawnActor, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            debug_mode=debug_mode,
                                            criteria_enable=criteria_enable)

    @staticmethod
    def actor_displayname(actor):
        return f"{get_actor_display_name(actor)}_{actor.id}"
    
    @staticmethod
    def get_heading(compass):
        heading = 'N' if compass > 270.5 or compass < 89.5 else ''
        heading += 'S' if 90.5 < compass < 269.5 else ''
        heading += 'E' if 0.5 < compass < 179.5 else ''
        heading += 'W' if 180.5 < compass < 359.5 else ''
        return heading
    
    def _initialize_actors(self, config):
        logger.debug_s(f"Initializing actor: {self.model_names}")
        total_amount = self.total_amount
        amount_round_down = total_amount // len(self.model_names)

        for idx, model_name in enumerate(self.model_names):
            amount = total_amount if idx == len(self.model_names) - 1 else amount_round_down
            total_amount -= amount

            report_string = f"Spawning model: {model_name} with amount: {amount} "
            new_actors = CarlaDataProvider.request_new_batch_actors(model_name,
                                                                    amount,
                                                                    carla.Transform(),
                                                                    autopilot=True,
                                                                    random_location=True,
                                                                    rolename='background')

            if new_actors is None:
                raise Exception("Error: Unable to add the background activity, all spawn points were occupied")


            report_string += f"amount spawned: {len(new_actors)}"
            print(report_string)
            self.other_actors.extend(new_actors)

    def _create_behavior(self):
        """
        Ego vehicle passes the start-trigger point
        Multiple actor(s) spawned and drive autopilot-ly
        Optional: Ego vehicle passes the end-trigger point or x-distance
        """

        # leaf nodes
        start_condition = None
        if self._ego_route is not None:
            start_condition = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0],
                                                                    self._ego_route,
                                                                    self._trigger_location,
                                                                    self._dist_to_trigger)

        end_condition = None
        if self._ego_vehicle_distance_driven > 0:
            end_condition = DriveDistance(self.ego_vehicles[0],
                                        self._ego_vehicle_distance_driven,
                                        name="End condition ego drive distance")
        
        other_actors_transform = []
        other_actors_stop_on = []
        other_actors_stop_off = []
        other_actors_autopilot_on = []
        other_actors_behaviors = []
        other_actors_remove = []
        for _, other_actor in enumerate(self.other_actors):
            transform = other_actor.get_transform()
            other_actor_transform = ActorTransformSetter(other_actor, 
                                                         carla.Transform(carla.Location(transform.location.x,
                                                                                        transform.location.y,
                                                                                        transform.location.z + self.underground_z), 
                                                                         transform.rotation),
                                                         name=f"TransformSetterActor {other_actor.id}",
                                                         physics=True)
            
            other_actor_remove = ActorDestroy(other_actor, name=f"Destroy actor {other_actor.id}")
            other_actor_stop_on = StopVehicle(other_actor, 1, name=f"Stop on {other_actor.id}")
            other_actor_stop_off = StopVehicle(other_actor, 0, name=f"Stop off {other_actor.id}")
            
            if isinstance(other_actor, carla.Vehicle):
                other_actor_autopilot_on = ChangeAutoPilot(other_actor, True, name=f"Autopilot on {other_actor.id}")

            # building other actor tree
            horn_behavior = HornBehavior(self.ego_vehicles[0],
                                         other_actor,
                                         name=f"Horn behavior {other_actor.id}") # using default in horn and out horn behavior

            other_actors_transform.append(other_actor_transform)
            other_actors_behaviors.append(horn_behavior)
            other_actors_remove.append(other_actor_remove)

            if isinstance(other_actor, carla.Vehicle):
                other_actors_stop_on.append(other_actor_stop_on)
                other_actors_stop_off.append(other_actor_stop_off)
                other_actors_autopilot_on.append(other_actor_autopilot_on)           

        # non leaf nodes
        other_actors_transform_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, 
                                                               name="Other actors transform")
        other_actors_stop_on_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, 
                                                               name="Other actors stop on")
        other_actors_stop_off_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, 
                                                               name="Other actors stop off")
        other_actors_autopilot_on_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, 
                                                               name="Other actors autopilot")
        other_actors_behavior_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL,
                                                                name="Other actors behavior")
        other_actors_remove_parallel = py_trees.composites.Parallel(policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL,
                                                                name="Other actors remove")
        
        other_actors_transform_parallel.add_children(other_actors_transform)
        other_actors_stop_on_parallel.add_children(other_actors_stop_on)
        other_actors_stop_off_parallel.add_children(other_actors_stop_off)
        other_actors_autopilot_on_parallel.add_children(other_actors_autopilot_on)
        other_actors_behavior_parallel.add_children(other_actors_behaviors)
        other_actors_remove_parallel.add_children(other_actors_remove)

        root = Sequence(name=self.__class__.__name__)

        if self._ego_route is not None:
            # init: other actors: make visible, brake on
            initialization = Sequence(name="Initialization")
            initialization.add_child(other_actors_transform_parallel)
            initialization.add_child(other_actors_stop_on_parallel)
            root.add_child(initialization)

            # pre start: other actors: idle until start condition triggered
            prestart = Parallel(name="Prestart", policy=ParallelPolicy.SUCCESS_ON_ONE)
            prestart.add_children([Idle(), start_condition])
            root.add_child(prestart)

        # on start: other actors: brake off
        onstart = Sequence(name="Onstart")
        onstart.add_children([other_actors_autopilot_on_parallel, other_actors_stop_off_parallel])
        root.add_child(onstart)

        # main: other actors: behavior until end condition triggered
        main = Parallel(name="Main", policy=ParallelPolicy.SUCCESS_ON_ONE)
        main.add_child(other_actors_behavior_parallel)
        if end_condition:
            main.add_child(end_condition)
        root.add_child(main)

        end = Sequence(name="End")
        end.add_child(other_actors_remove_parallel)
        root.add_child(end)

        if self.do_print:
            py_trees.display.render_dot_tree(root, name=os.path.join(OUT_DIR, __class__.__name__))
            self.do_print = False

        return root

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


class SpawnActorOnTrigger(SpawnActor):
    """
    Spawn batch actor(s) with single model on a trigger location
    """
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False, model_names=['vehicle.*'], total_amount=50):
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super().__init__(world, ego_vehicles, config, randomize=randomize, debug_mode=debug_mode, timeout=timeout, criteria_enable=criteria_enable, model_names=model_names, total_amount=total_amount)

    def _put_other_actors_under(self):
        def _freeze_vehicle(vehicle):
            vehicle.set_autopilot(False)
            vehicle.set_simulate_physics(enabled=False)

        for other_actor in self.other_actors:
            location = other_actor.get_location()
            uground_location = carla.Location(location.x,
                                              location.y,
                                              location.z - self.underground_z)
            other_actor.set_location(uground_location)

            if isinstance(other_actor, carla.Vehicle):
                _freeze_vehicle(other_actor)

    def _move_actors_in_trigger_location(self):
        def new_transform_in_same_lane(transform, trigger_location):
            movement_distance = 20
            heading = SpawnActor.get_heading(transform.rotation.yaw)
            delta_x = delta_y = delta_z = 0
            if heading.startswith('N'):
                delta_x += movement_distance
            if heading.startswith('S'):
                delta_x -= movement_distance
            if heading.endswith('E'):
                delta_y += movement_distance
            if heading.endswith('W'):
                delta_y -= movement_distance
            return carla.Transform(carla.Location(trigger_location.x + delta_x,
                                                  trigger_location.y + delta_y,
                                                  transform.location.z + delta_z),
                                   transform.rotation)
        
        # move vehicle that spawns in the trigger posision: forward
        distance_threshold = 20
        trigger_position = CarlaDataProvider.get_map().get_waypoint(self._trigger_location)
        trigger_lane_id = trigger_position.lane_id
        for other_actor in self.other_actors:
            transform = other_actor.get_transform()
            location = other_actor.get_location()
            current_position_actor = CarlaDataProvider.get_map().get_waypoint(location)
            current_lane_id = current_position_actor.lane_id
            if current_lane_id != trigger_lane_id:
                continue
            
            actor_dn = SpawnActor.actor_displayname(other_actor)
            distance = location.distance(self._trigger_location)
            if distance < distance_threshold:
                # batch_delete.append(actor.id)
                logger.debug_s(f"{actor_dn} on {location} to {self._trigger_location} distance {distance}")
                new_transform = new_transform_in_same_lane(transform, self._trigger_location)
                if transform == new_transform:
                    continue

                other_actor.set_location(new_transform.location)
                logger.debug_s(f"{other_actor.id} moved from {transform.location} to {new_transform.location}")
        
        # sync state
        if CarlaDataProvider.is_sync_mode():
            CarlaDataProvider.get_world().tick()
        else:
            CarlaDataProvider.get_world().wait_for_tick()

    def _initialize_actors(self, config):        
        super()._initialize_actors(config)
        self._move_actors_in_trigger_location()
        # put all actors underground
        self._put_other_actors_under()