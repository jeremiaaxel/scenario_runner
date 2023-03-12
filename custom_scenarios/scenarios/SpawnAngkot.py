#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import logging
from custom_scenarios.scenarios.SpawnActors import SpawnActors, SpawnActorsOnTrigger

logger = logging.getLogger(__name__)
angkot_model_name = 'vehicle.angkot.angkot'

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
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_name=angkot_model_name)


class SpawnAngkotOnTrigger(SpawnActorsOnTrigger):
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        super(SpawnAngkotOnTrigger, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_name=angkot_model_name)