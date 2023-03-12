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
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeAutoPilot, ActorTransformSetter, KeepVelocity, ActorDestroy, HandBrakeVehicle
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance, InTimeToArrivalToVehicle, InTriggerDistanceToLocationAlongRoute

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
        logger.debug_s("Initializing actor")
        new_actors = CarlaDataProvider.request_new_batch_actors(self.model_name,
                                                                self.amount,
                                                                carla.Transform(),
                                                                autopilot=True,
                                                                random_location=True,
                                                                rolename='background')

        if new_actors is None:
            raise Exception("Error: Unable to add the background activity, all spawn points were occupied")

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


class SpawnActorsOnTrigger(SpawnActors):
    underground_z = 500
    _other_actor_target_velocity = 5
    _ego_vehicle_distance_driven = 40
    amount = 30

    def _put_other_actors_under(self):
        for other_actor in self.other_actors:
            location = other_actor.get_location()
            uground_location = carla.Location(location.x,
                                location.y,
                                location.z - self.underground_z)
            other_actor.set_location(uground_location)
            other_actor.set_simulate_physics(enabled=False)

    def _move_actors_in_trigger_location(self):
        def new_transform_in_same_lane(transform):
            movement_distance = 20
            heading = SpawnActors.get_heading(transform.rotation.yaw)
            delta_x = delta_y = delta_z = 0
            if heading.startswith('N'):
                delta_x += movement_distance
            if heading.startswith('S'):
                delta_x -= movement_distance
            if heading.endswith('E'):
                delta_y += movement_distance
            if heading.endswith('W'):
                delta_y -= movement_distance
            return carla.Transform(carla.Location(transform.location.x + delta_x,
                                                  transform.location.y + delta_y,
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
            
            actor_dn = SpawnActors.actor_displayname(other_actor)
            logger.debug_s(f"Actor {actor_dn} spawns on the same lane with trigger location")
            distance = location.distance(self._trigger_location)
            if distance < distance_threshold:
                # batch_delete.append(actor.id)
                logger.debug_s(f"{actor_dn} spawns on the ego vehicle trigger location")
                new_transform = new_transform_in_same_lane(transform)
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
        Multiple angkot(s) spawned and drive autopilot-ly
        Optional: Ego vehicle passes the end-trigger point or x-distance
        """
        root = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="SpawnAngkotOnTrigger")

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

        angkots_velocity = []
        angkots_remove = []
        angkots_transform = []
        angkots_brake_on = []
        angkots_brake_off = []
        angkots_autopilot = []
        for idx, other_actor in enumerate(self.other_actors):
            transform = other_actor.get_transform()
            angkot_transform = ActorTransformSetter(other_actor, 
                carla.Transform(
                    carla.Location(transform.location.x,
                                    transform.location.y,
                                    transform.location.z + self.underground_z), 
                    transform.rotation),
                name=f"TransformSetterAngkot_{idx}",
                physics=True)
            actor_velocity = KeepVelocity(other_actor,
                                      self._other_actor_target_velocity,
                                      name="angkot velocity")
            actor_remove = ActorDestroy(other_actor,
                                        name="Destroying angkot")
            
            angkots_transform.append(angkot_transform)
            angkots_autopilot.append(ChangeAutoPilot(other_actor, True))
            angkots_brake_on.append(HandBrakeVehicle(other_actor, True))
            angkots_brake_off.append(HandBrakeVehicle(other_actor, False))
            angkots_remove.append(actor_remove)
            angkots_velocity.append(actor_velocity)
            
        end_condition = DriveDistance(self.ego_vehicles[0],
                                    self._ego_vehicle_distance_driven,
                                    name="End condition ego drive distance")

        # non leaf nodes
        scenario_sequence = py_trees.composites.Sequence()
        keep_velocity_angkots = py_trees.composites.Parallel(
                policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE, name="keep velocity angkots")

        # building tree
        root.add_child(scenario_sequence)
        scenario_sequence.add_children(angkots_transform)
        scenario_sequence.add_children(angkots_brake_on)
        scenario_sequence.add_child(start_condition)
        scenario_sequence.add_children(angkots_brake_off)
        scenario_sequence.add_child(keep_velocity_angkots)
        scenario_sequence.add_children(angkots_remove)
        scenario_sequence.add_child(end_condition)

        keep_velocity_angkots.add_children(angkots_autopilot)
        keep_velocity_angkots.add_children(angkots_velocity)

        return root
