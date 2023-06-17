#!/usr/bin/env python

#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Scenario spawning elements to make the town dynamic and interesting
"""

import logging
from customs.helpers.blueprints import create_blueprints_by_attribute, distribute_amounts
from customs.scenarios.spawn_actor import SpawnActor, SpawnActorOnTrigger
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

logger = logging.getLogger(__name__)

total_amount = 30

class SpawnBike(SpawnActor):

    """
    Implementation of a scenario to spawn a set of background actors,
    and to remove traffic jams in background traffic

    This is a single ego vehicle scenario
    """
    @classmethod
    def get_modelnames_and_amounts(cls):
        total_amount = 50
        two_wheel_blueprints = create_blueprints_by_attribute("number_of_wheels", 2)
        two_wheel_modelnames = [bp.id for bp in two_wheel_blueprints]
        amounts = distribute_amounts(total_amount, len(two_wheel_modelnames))
        return two_wheel_modelnames, amounts


    def __init__(self,
                 world,
                 ego_vehicles,
                 config,
                 randomize=True,
                 debug_mode=False,
                 timeout=35 * 60,
                 criteria_enable=False,
                 amounts=[total_amount]):
        """
        Setup all relevant parameters and create scenario
        """
        modelnames, amounts = __class__.get_modelnames_and_amounts()

        super(SpawnBike, self).__init__(world,
                                        ego_vehicles,
                                        config,
                                        randomize,
                                        debug_mode=debug_mode,
                                        timeout=timeout,
                                        criteria_enable=criteria_enable,
                                        model_names=modelnames,
                                        amounts=amounts)


class SpawnBikeOnTrigger(SpawnBike, SpawnActorOnTrigger):
    pass