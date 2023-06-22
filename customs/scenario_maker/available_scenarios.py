import random
from typing import Dict, List, Tuple

from customs.scenarios.obstructing_actor import (
    ObstructingVehicleHorn, ObstructingVehicleTimer,
    ObstructingPedestrianHorn, ObstructingPedestrianTimer
)
from customs.scenarios.crossing_pedestrian import CrossingPedestrianCyclist, CrossingPedestrianCyclistProps
from customs.scenarios.spawn_car import SpawnCarOnTrigger
from customs.scenarios.spawn_mixed import SpawnMixedOnTrigger
from customs.scenarios.spawn_still_walkers import SpawnStillWalkers
from customs.scenarios.spawn_actor import SpawnActorOnTrigger
from customs.scenarios.spawn_angkot import SpawnAngkotOnTrigger
from customs.scenarios.spawn_bike import SpawnBikeOnTrigger
from customs.scenarios.spawn_pedestrian import SpawnPedestrianOnTrigger
from customs.scenarios.time import TimeDay, TimeNight, TimeSunrise
from customs.scenarios.weather import get_weather_scenario
from customs.scenarios.cut_in import CutInRoute
from customs.helpers.blueprints import modify_class
from collections import OrderedDict

from srunner.scenarios.basic_scenario import BasicScenario


class AvailableScenarios(object):
    """
    A class the contains all available scenarios.
    All scenarios are defined as ordered dictionary.
    """
    WEATHER_SCENARIOS: Dict[str, Dict[str, BasicScenario]] = {
        'cloudy': OrderedDict([
            ("Cloudy", get_weather_scenario('cloudy')),
            ("Overcast", get_weather_scenario('overcast')),
        ]),
        'foggy': OrderedDict([
            ("Foggy", get_weather_scenario('foggy')),
            ("HeavyFoggy", get_weather_scenario('heavyfoggy')),
        ]),
        'clear': OrderedDict([("Clear", get_weather_scenario('clear'))]),
        'rain': OrderedDict([
            ("HardRain", get_weather_scenario('hardrain')),
            ("Rain", get_weather_scenario('rain')),
        ])
    }

    TIME_SCENARIOS: Dict[str, Dict[str, BasicScenario]] = {
        'night': OrderedDict([("Night", TimeNight)]),
        'day': OrderedDict([('Day', TimeDay)]),
        'sunrise': OrderedDict([("Sunrise", TimeSunrise)])
    }

    # Spawning Scenarios but never ending
    BACKGROUND_SCENARIOS: Dict[str, Dict[str, BasicScenario]] = {
        'fourwheel': OrderedDict([
            ("SpawnAngkotOnTriggerBackground", modify_class(
                SpawnAngkotOnTrigger, _ego_vehicle_distance_drive=-1)),
        ]),
        'twowheel': OrderedDict([
            ("SpawnBikeOnTriggerBackground", modify_class(
                SpawnBikeOnTrigger, _ego_vehicle_distance_drive=-1)),
        ]),
        'pedestrian': OrderedDict([
            ("SpawnPedestrianOnTriggerBackground", modify_class(
                SpawnPedestrianOnTrigger, _ego_vehicle_distance_drive=-1)),
        ]),
        'mixed': OrderedDict([
            # ("SpawnActorOnTriggerBackground", modify_class(
            #     SpawnActorOnTrigger, _ego_vehicle_distance_driven=-1)),
            ("SpawnMixedOnTriggerBackground", modify_class(
                SpawnMixedOnTrigger, _ego_vehicle_distance_drive=-1)),
            ])
    }

    # Background scenarios but ending on ego drive distance
    SPAWNING_SCENARIOS: Dict[str, Dict[str, BasicScenario]] = {
        'fourwheel': OrderedDict([
            ("SpawnAngkotOnTrigger", SpawnAngkotOnTrigger),
            ("SpawnCarOnTrigger", SpawnCarOnTrigger),
        ]),
        'twowheel': OrderedDict([
            ("SpawnBikeOnTrigger", SpawnBikeOnTrigger),
        ]),
        'pedestrian': OrderedDict([
            ("SpawnPedestrianOnTrigger", SpawnPedestrianOnTrigger),
        ]),
        'mixed': OrderedDict([
            # ("SpawnActorOnTrigger", SpawnActorOnTrigger),
            ("SpawnMixedOnTrigger", SpawnMixedOnTrigger),
        ])
    }

    OTHER_SCENARIOS: Dict[str, Dict[str, BasicScenario]] = {
        'crossing': OrderedDict([
            ("CrossingPedestrianFar", modify_class(CrossingPedestrianCyclist,
                                                   custom_name="PedestrianFarCrossing",
                                                   adversary_type=False,
                                                   _start_distance=CrossingPedestrianCyclistProps.DISTANCE_FAR,
                                                   custom_speed=CrossingPedestrianCyclistProps.SPEED_NORMAL)),
            ("CrossingPedestrianClose", modify_class(CrossingPedestrianCyclist,
                                                     custom_name="PedestrianCloseCrossing",
                                                     adversary_type=False,
                                                     _start_distance=CrossingPedestrianCyclistProps.DISTANCE_CLOSE,
                                                     custom_speed=CrossingPedestrianCyclistProps.SPEED_NORMAL)),
            ("CrossingCyclistFar", modify_class(CrossingPedestrianCyclist,
                                                custom_name="CyclistFarCrossing",
                                                adversary_type=True,
                                                _start_distance=CrossingPedestrianCyclistProps.DISTANCE_FAR,
                                                custom_speed=CrossingPedestrianCyclistProps.SPEED_NORMAL)),
            ("CrossingCyclistClose", modify_class(CrossingPedestrianCyclist,
                                                  custom_name="CyclistCloseCrossing",
                                                  adversary_type=True,
                                                  _start_distance=CrossingPedestrianCyclistProps.DISTANCE_CLOSE,
                                                  custom_speed=CrossingPedestrianCyclistProps.SPEED_NORMAL)),
            ("CrossingPedestrianSlowFar", modify_class(CrossingPedestrianCyclist,
                                                       custom_name="PedestrianSlowFarCrossing",
                                                       adversary_type=False,
                                                       _start_distance=CrossingPedestrianCyclistProps.DISTANCE_FAR,
                                                       custom_speed=CrossingPedestrianCyclistProps.SPEED_SLOW)),
            ("CrossingPedestrianSlowClose", modify_class(CrossingPedestrianCyclist,
                                                         custom_name="PedestrianSlowCloseCrossing",
                                                         adversary_type=False,
                                                         _start_distance=CrossingPedestrianCyclistProps.DISTANCE_CLOSE,
                                                         custom_speed=CrossingPedestrianCyclistProps.SPEED_SLOW)),
            ("CrossingCyclistSlowFar", modify_class(CrossingPedestrianCyclist,
                                                    custom_name="CyclistSlowFarCrossing",
                                                    adversary_type=True,
                                                    _start_distance=CrossingPedestrianCyclistProps.DISTANCE_FAR,
                                                    custom_speed=CrossingPedestrianCyclistProps.SPEED_SLOW)),
            ("CrossingCyclistSlowClose", modify_class(CrossingPedestrianCyclist,
                                                      custom_name="CyclistSlowCloseCrossing",
                                                      adversary_type=True,
                                                      _start_distance=CrossingPedestrianCyclistProps.DISTANCE_CLOSE,
                                                      custom_speed=CrossingPedestrianCyclistProps.SPEED_SLOW)),
            ("CrossingPedestrianRandom", modify_class(CrossingPedestrianCyclist,
                                                      custom_name="PedestrianRandomCrossing",
                                                      adversary_type=False,
                                                      _start_distance=CrossingPedestrianCyclistProps.DISTANCE_RANDOM,
                                                      custom_speed=CrossingPedestrianCyclistProps.SPEED_RANDOM)),
            ("CrossingCyclistRandom", modify_class(CrossingPedestrianCyclist,
                                                   custom_name="CyclistRandomCrossing",
                                                   adversary_type=True,
                                                   _start_distance=CrossingPedestrianCyclistProps.DISTANCE_RANDOM,
                                                   custom_speed=CrossingPedestrianCyclistProps.SPEED_RANDOM))
        ]),
        "obstructing": OrderedDict([
            ("ObstructingVehicleHorn", ObstructingVehicleHorn),
            ("ObstructingVehicleTimer", ObstructingVehicleTimer),
            ("ObstructingPedestrianHorn", ObstructingPedestrianHorn),
            ("ObstructingPedestrianTimer", ObstructingPedestrianTimer),
        ]),
        "cutin": OrderedDict([
            ("CutInRoute", CutInRoute)
        ]),
        # TODO: CarCrossingOnJunction
        # TODO: BikeCrossingOnJunction
        # "spawnstill": OrderedDict([
        #     # For Regression
        #     ("SpawnStillWalkers", SpawnStillWalkers),
        # ])
    }

    @staticmethod
    def __get_scenarios(scenarios_category: Dict[str, Dict[str, BasicScenario]], randomize=True):
        scenarios = list()
        for subcategory in scenarios_category.values():
            scenarios.extend(list(subcategory.items()))
        
        if randomize:
            random.shuffle(scenarios)
        return OrderedDict(scenarios)
    
    @classmethod
    def get_weather_scenarios(cls, randomize=True):
        """
        Get weather scenarios
        :param
            randomize: randomize the order of the dict (default: True)
        """
        return cls.__get_scenarios(cls.WEATHER_SCENARIOS, randomize=randomize)

    @classmethod
    def get_time_scenarios(cls, randomize=True):
        """
        Get time scenarios
        :param
            randomize: randomize the order of the dict (default: True)
        """
        return cls.__get_scenarios(cls.TIME_SCENARIOS, randomize=randomize)

    @classmethod
    def get_other_scenarios(cls, randomize=True):
        """
        Get other scenarios
        :param
            randomize: randomize the order of the dict (default: True)
        """
        return cls.__get_scenarios(cls.OTHER_SCENARIOS, randomize=randomize)

    @classmethod
    def get_background_scenarios(cls, randomize=True):
        """
        Get spawning scenarios but neverending as background scenario
        :param
            randomize: randomize the order of the dict (default: True)
        """
        return cls.__get_scenarios(cls.BACKGROUND_SCENARIOS, randomize=randomize)

    @classmethod
    def get_spawning_scenarios(cls, randomize=True):
        """
        Get spawning scenarios
        :param
            randomize: randomize the order of the dict (default: True)
        """
        return cls.__get_scenarios(cls.SPAWNING_SCENARIOS, randomize=randomize)
    
    @staticmethod
    def __get_one_each_subcategory(category: Dict[str, Dict[str, BasicScenario]]) -> List[Tuple[str, BasicScenario]]:
        scenarios = []
        for subcategory in category.values():
            subcateg_scenarios = list(subcategory.items())
            scenarios.append(random.choice(subcateg_scenarios))
        return scenarios

    @classmethod
    def get_validation_scenarios(cls):
        validation_scenarios = OrderedDict()
        validation_scenarios.update(cls.__get_one_each_subcategory(cls.SPAWNING_SCENARIOS))
        validation_scenarios.update(cls.__get_one_each_subcategory(cls.WEATHER_SCENARIOS))
        validation_scenarios.update(cls.__get_one_each_subcategory(cls.TIME_SCENARIOS))
        validation_scenarios.update(cls.__get_one_each_subcategory(cls.OTHER_SCENARIOS))
        return validation_scenarios

    @classmethod
    def get_all_scenarios(cls, randomize=True, no_background=False):
        """
        Get all scenarios.
        :param
            randomize: randomize the order of the dict (default: True)
            no_background: not including background scenarios (nonending spawn) (default: False)
        """
        all_scenarios_odict = OrderedDict()
        if not no_background:
            all_scenarios_odict.update(
                cls.get_background_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_spawning_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_weather_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_time_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_other_scenarios(randomize=False))
        all_scenarios = list(all_scenarios_odict.items())
        if randomize:
            random.shuffle(all_scenarios)
        return OrderedDict(all_scenarios)
