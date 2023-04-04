#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import logging
from customs.helpers.blueprints import create_blueprints_by_attribute
from customs.scenarios.SpawnActor import SpawnActor, SpawnActorOnTrigger

logger = logging.getLogger(__name__)

total_amount = 30

class SpawnBike(SpawnActor):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        """
        Setup all relevant parameters and create scenario
        """
        two_wheel_blueprints = create_blueprints_by_attribute("number_of_wheels", 2)
        two_wheel_modelnames = [bp.id for bp in two_wheel_blueprints]
        logger.debug_s(two_wheel_modelnames)
        super(SpawnBike, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_names=two_wheel_modelnames,
                                            total_amount=total_amount)

class SpawnBikeOnTrigger(SpawnActorOnTrigger):
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, timeout=35 * 60, criteria_enable=False):
        two_wheel_blueprints = create_blueprints_by_attribute("number_of_wheels", 2)
        two_wheel_modelnames = [bp.id for bp in two_wheel_blueprints]
        logger.debug_s(two_wheel_modelnames)
        super(SpawnBikeOnTrigger, self).__init__(world,
                                            ego_vehicles,
                                            config,
                                            randomize,
                                            debug_mode=debug_mode,
                                            timeout=timeout,
                                            criteria_enable=criteria_enable,
                                            model_names=two_wheel_modelnames,
                                            total_amount=total_amount)