#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import logging
import py_trees

import carla

from custom_scenarios.scenarios.SpawnActors import SpawnActors
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import AccelerateToVelocity, ActorDestroy, ActorTransformSetter, ChangeAutoPilot, HandBrakeVehicle, KeepVelocity, StopVehicle
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance, InTimeToArrivalToVehicle, InTriggerDistanceToLocationAlongRoute
from srunner.tools.scenario_helper import get_location_in_distance_from_wp

logger = logging.getLogger(__name__)

class SpawnAngkot(SpawnActors):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        """
        Setup all relevant parameters and create scenario
        """
        super(SpawnAngkot, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            debug_mode=debug_mode,
                                            criteria_enable=criteria_enable,
                                            model_name='vehicle.angkot.angkot')


class SpawnAngkotOnTrigger(SpawnAngkot):
    underground_z = 500
    _other_actor_target_velocity = 5
    _ego_vehicle_distance_driven = 40
    amount = 30

    def _put_other_actors_under(self):
        for other_actor in self.other_actors:
            transform = other_actor.get_transform()
            underground_transform = carla.Transform(
                carla.Location(transform.location.x,
                                transform.location.y,
                                transform.location.z - self.underground_z), 
                transform.rotation)
            other_actor.set_transform(underground_transform)
            other_actor.set_simulate_physics(enabled=False)

    def _initialize_actors(self, config):
        super()._initialize_actors(config)
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

        dist_to_trigger = 12
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
