#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import time
import carla
import py_trees
import logging
from multisensors.utils.manual_control_global_funcs import get_actor_display_name

from srunner.scenarios.background_activity import BackgroundActivity
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot, ActorTransformSetter, KeepLongitudinalGap, KeepVelocity, ActorDestroy, HandBrakeVehicle
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance, InTimeToArrivalToVehicle, InTriggerDistanceToLocationAlongRoute

logger = logging.getLogger(__name__)

class SpawnActor(BackgroundActivity):
    """
    Spawn batch actor(s) with multiple model filter
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False, model_names=['vehicle.*'], total_amount=50):
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
            if idx == len(self.model_names) - 1:
                amount = total_amount
            else:
                amount = amount_round_down
                
            total_amount -= amount

            new_actors = CarlaDataProvider.request_new_batch_actors(model_name,
                                                                    amount,
                                                                    carla.Transform(),
                                                                    autopilot=True,
                                                                    random_location=True,
                                                                    rolename='background')

            if new_actors is None:
                raise Exception("Error: Unable to add the background activity, all spawn points were occupied")

            print(f"{model_name} spawned: {len(new_actors)}")
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

class SpawnActorOnTrigger(SpawnActor):
    """
    Spawn batch actor(s) with single model on a trigger location
    """

    underground_z = 500
    _other_actor_target_velocity = 5
    _ego_vehicle_distance_driven = 40

    def _put_other_actors_under(self):
        for other_actor in self.other_actors:
            location = other_actor.get_location()
            uground_location = carla.Location(location.x,
                                location.y,
                                location.z - self.underground_z)
            other_actor.set_location(uground_location)
            other_actor.set_simulate_physics(enabled=False)

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

    def _create_behavior(self):
        """
        Ego vehicle passes the start-trigger point
        Multiple actor(s) spawned and drive autopilot-ly
        Optional: Ego vehicle passes the end-trigger point or x-distance
        """
        root = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="SpawnActorOnTrigger")

        dist_to_trigger = 0
        # leaf nodes
        if self._ego_route is not None:
            start_condition = InTriggerDistanceToLocationAlongRoute(self.ego_vehicles[0],
                                                                    self._ego_route,
                                                                    self._trigger_location,
                                                                    dist_to_trigger)
        else:
            start_condition = InTimeToArrivalToVehicle(self.ego_vehicles[0],
                                                       self.other_actors[0],
                                                       self._time_to_reach)

        actors_remove = []
        actors_transform = []
        actors_brake_on = []
        actors_brake_off = []
        actors_autopilot = []
        for idx, other_actor in enumerate(self.other_actors):
            transform = other_actor.get_transform()
            actor_transform = ActorTransformSetter(other_actor, 
                carla.Transform(
                    carla.Location(transform.location.x,
                                    transform.location.y,
                                    transform.location.z + self.underground_z), 
                    transform.rotation),
                name=f"TransformSetterActor_{idx}",
                physics=True)
            actor_velocity = KeepVelocity(other_actor,
                                      self._other_actor_target_velocity,
                                      name="actor velocity")
            actor_remove = ActorDestroy(other_actor,
                                        name="Destroying actor")
            
            actors_transform.append(actor_transform)
            actors_autopilot.append(ChangeAutoPilot(other_actor, True))
            actors_brake_on.append(HandBrakeVehicle(other_actor, True))
            actors_brake_off.append(HandBrakeVehicle(other_actor, False))
            actors_remove.append(actor_remove)
            
        end_condition = DriveDistance(self.ego_vehicles[0],
                                    self._ego_vehicle_distance_driven,
                                    name="End condition ego drive distance")

        # non leaf nodes
        scenario_sequence = py_trees.composites.Sequence()
        actors_autopilot_nodes = py_trees.composites.Parallel(
                policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="keep velocity actors")

        # building tree
        root.add_child(scenario_sequence)
        scenario_sequence.add_children(actors_transform)
        scenario_sequence.add_children(actors_brake_on)
        scenario_sequence.add_child(start_condition)
        scenario_sequence.add_children(actors_brake_off)
        scenario_sequence.add_child(actors_autopilot_nodes)
        scenario_sequence.add_children(actors_remove)
        scenario_sequence.add_child(end_condition)

        actors_autopilot_nodes.add_children(actors_autopilot)

        return root
