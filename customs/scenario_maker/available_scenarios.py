import random
from customs.scenarios.obstructing_actor import (
    ObstructingVehicleHorn, ObstructingVehicleTimer,
    ObstructingPedestrianHorn, ObstructingPedestrianTimer
)
from customs.scenarios.crossing_pedestrian import CrossingPedestrianCyclist, CrossingPedestrianCyclistProps
from customs.scenarios.spawn_mixed import SpawnMixedOnTrigger
from customs.scenarios.spawn_still_walkers import SpawnStillWalkers
from customs.scenarios.spawn_actor import SpawnActorOnTrigger
from customs.scenarios.spawn_angkot import SpawnAngkotOnTrigger
from customs.scenarios.spawn_bike import SpawnBikeOnTrigger
from customs.scenarios.spawn_pedestrian import SpawnPedestrianOnTrigger
from customs.scenarios.time import TimeDay, TimeNight, TimeSunrise
from customs.scenarios.weather import get_weather_scenario
# (
#     WeatherClear, WeatherHardRain, WeatherOvercast,
#     # Presets
#     WeatherClearSunsetRoute, WeatherWetNoonRoute, 
#     WeatherHardRainNightRoute, WeatherRainyDayRoute, 
#     WeatherMidRainyNoonRoute
# )
from customs.scenarios.cut_in import CutInRoute
from customs.helpers.blueprints import modify_class
from collections import OrderedDict

class AvailableScenarios(object): 
    WEATHER_SCENARIOS = OrderedDict([
        ("Overcast", get_weather_scenario('overcast')),
        ("Foggy", get_weather_scenario('foggy')),
        ("HeavyFoggy", get_weather_scenario('heavyfoggy')),
        ("Clear", get_weather_scenario('clear')),
        ("HardRain", get_weather_scenario('hardrain')),
        ("Rain", get_weather_scenario('rain')),
    ])

    TIME_SCENARIOS = OrderedDict([
        ("Night", TimeNight),
        ("Day", TimeDay),
        ("Sunrise", TimeSunrise)
    ])

    BACKGROUND_SCENARIOS = OrderedDict([
        # Spawning(s)
        # "SpawnAngkot": SpawnAngkot,
        # "SpawnBike": SpawnBike,
        # "SpawnPedestrian": SpawnPedestrian,
        # "SpawnMixed": SpawnMixed,
        ("SpawnActorOnTrigger", SpawnActorOnTrigger),
        ("SpawnAngkotOnTrigger", SpawnAngkotOnTrigger),
        ("SpawnBikeOnTrigger", SpawnBikeOnTrigger),
        ("SpawnPedestrianOnTrigger", SpawnPedestrianOnTrigger),
        ("SpawnMixedOnTrigger", SpawnMixedOnTrigger)
    ])

    OTHER_SCENARIOS = OrderedDict([
        # Crossings(s)
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
                                                          custom_speed=CrossingPedestrianCyclistProps.SPEED_RANDOM)),
        # TODO: CarCrossingOnJunction
        # TODO: BikeCrossingOnJunction

        # Obstructing(s)
        ("ObstructingVehicleHorn", ObstructingVehicleHorn),
        ("ObstructingVehicleTimer", ObstructingVehicleTimer),
        # TODO: Fix obstructing pedestrian
        ("ObstructingPedestrianHorn", ObstructingPedestrianHorn),
        ("ObstructingPedestrianTimer", ObstructingPedestrianTimer),
        
        # For Regression
        ("SpawnStillWalkers", SpawnStillWalkers),

        ("CutInRoute", CutInRoute)
    ])

    @classmethod
    def get_weather_scenarios(cls, randomize=True):
        scenarios = list(cls.WEATHER_SCENARIOS.items())
        if randomize:
            random.shuffle(scenarios)
        return OrderedDict(scenarios)

    @classmethod
    def get_time_scenarios(cls, randomize=True):
        scenarios = list(cls.TIME_SCENARIOS.items())
        if randomize:
            random.shuffle(scenarios)
        return OrderedDict(scenarios)

    @classmethod
    def get_other_scenarios(cls, randomize=True):
        scenarios = list(cls.OTHER_SCENARIOS.items())
        if randomize:
            random.shuffle(scenarios)
        return OrderedDict(scenarios)

    @classmethod
    def get_background_scenarios(cls, randomize=True):
        scenarios = list(cls.BACKGROUND_SCENARIOS.items())
        if randomize:
            random.shuffle(scenarios)
        return OrderedDict(scenarios)

    @classmethod
    def get_all_scenarios(cls, randomize=True):
        all_scenarios_odict = OrderedDict()
        all_scenarios_odict.update(cls.get_background_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_weather_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_time_scenarios(randomize=False))
        all_scenarios_odict.update(cls.get_other_scenarios(randomize=False))
        all_scenarios = list(all_scenarios_odict.items())
        if randomize:
            random.shuffle(all_scenarios)
        return OrderedDict(all_scenarios)
