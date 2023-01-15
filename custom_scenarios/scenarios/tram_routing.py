#!/usr/bin/env python

# Copyright (c) 2019-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Simple freeride scenario. No action, no triggers. Ego vehicle can simply cruise around.
"""

"""
Coordinates
-114.4, 57.7, 180
-114.7, 75.3, 180

-57.2, 140.4, 90
61.2, 141.3, 90

109.4, 89.0, 0  
109.6, 45.2, 0

turn left
83.1, 13.3, 270
-26.7, 13.2, 270

turn right
-41.7, -2.1, 0
-41.4, -41.2, 0

turn left
-67.1, -68.9, 270
-113.8, -4.8, 180
-114.4, 44.3, 180
"""

import py_trees

from srunner.scenariomanager.scenarioatomics.atomic_behaviors import Idle
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenarios.basic_scenario import BasicScenario


class TramRouting(BasicScenario):

    """
    Implementation of a simple free ride scenario that consits only of the ego vehicle
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=10000000):
        """
        Setup all relevant parameters and create scenario
        """
        # Timeout of scenario in seconds
        self.timeout = timeout
        super(TramRouting, self).__init__("TramRouting",
                                       ego_vehicles,
                                       config,
                                       world,
                                       debug_mode,
                                       criteria_enable=criteria_enable)

    def _setup_scenario_trigger(self, config):
        """
        """
        return None

    def _create_behavior(self):
        """
        """
        sequence = py_trees.composites.Sequence("Sequence Behavior")
        sequence.add_child(Idle())
        return sequence

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        for ego_vehicle in self.ego_vehicles:
            collision_criterion = CollisionTest(ego_vehicle)
            criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()
