from customs.scenarios.obstructing_actor import (
    ObstructingVehicleHorn, ObstructingVehicleTimer,
    ObstructingPedestrianHorn, ObstructingPedestrianTimer
)
from customs.scenarios.pedestrian_crossing import PedestrianCyclistCrossing, PedestrianCyclistProps, pedestrian_crossing_wrapper
from customs.scenarios.regression import Regression
from customs.scenarios.spawn_actor import SpawnActorInFront, SpawnActorOnTrigger
from customs.scenarios.spawn_angkot import SpawnAngkot, SpawnAngkotOnTrigger
from customs.scenarios.spawn_bike import SpawnBike, SpawnBikeOnTrigger
from customs.scenarios.spawn_pedestrian import SpawnPedestrian, SpawnPedestrianInFront, SpawnPedestrianOnTrigger
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

class AvailableScenarios(object): 
    WEATHER_SCENARIOS = {
        # "WetNoon": WeatherWetNoonRoute,
        # "MidRainyNoon": WeatherMidRainyNoonRoute,
        # "HardRainNight": WeatherHardRainNightRoute,
        # "ClearSunset": WeatherClearSunsetRoute,
        # "WeatherRainyDay": WeatherRainyDayRoute,
        
        "Clear": get_weather_scenario('clear'),
        "Rain": get_weather_scenario('rain'),
        "HardRain": get_weather_scenario('hardrain'),
        "Overcast": get_weather_scenario('overcast'),
        "Foggy": get_weather_scenario('foggy'),
        "LightFoggy": get_weather_scenario('lightfoggy'),
    }

    TIME_SCENARIOS = {
        "Night": TimeNight,
        "Day": TimeDay,
        # "Sunrise": TimeSunrise, # tmpcmt: for video avoid too dark
    }

    BACKGROUND_SCENARIOS = {
        # Spawning(s)
        "SpawnActorOnTrigger": SpawnActorOnTrigger,
        # "SpawnAngkot": SpawnAngkot,
        "SpawnAngkotOnTrigger": SpawnAngkotOnTrigger,
        # "SpawnBike": SpawnBike,
        "SpawnBikeOnTrigger": SpawnBikeOnTrigger,
        # "SpawnPedestrian": SpawnPedestrian,
        "SpawnPedestrianOnTrigger": SpawnPedestrianOnTrigger,
    }

    OTHER_SCENARIOS = {
        # Crossings(s)
        "PedestrianFarCrossing": modify_class(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianFarCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "PedestrianCloseCrossing": modify_class(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianCloseCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "CyclistFarCrossing": modify_class(PedestrianCyclistCrossing,
                                                          custom_name="CyclistFarCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "CyclistCloseCrossing": modify_class(PedestrianCyclistCrossing,
                                                          custom_name="CyclistCloseCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
                                                          
        "PedestrianSlowFarCrossing": modify_class(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianSlowFarCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "PedestrianSlowCloseCrossing": modify_class(custom_name="PedestrianSlowCloseCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "CyclistSlowFarCrossing": modify_class(PedestrianCyclistCrossing,
                                                          custom_name="CyclistSlowFarCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "CyclistSlowCloseCrossing": modify_class(PedestrianCyclistCrossing,
                                                          custom_name="CyclistSlowCloseCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        # TODO: CarCrossingOnJunction
        # TODO: BikeCrossingOnJunction

        # Obstructing(s)
        "ObstructingVehicleHorn": ObstructingVehicleHorn,
        "ObstructingVehicleTimer": ObstructingVehicleTimer,
        # TODO: Fix obstructing pedestrian
        "ObstructingPedestrianHorn": ObstructingPedestrianHorn,
        "ObstructingPedestrianTimer": ObstructingPedestrianTimer,
        # # For testing
        # "SpawnPedestrianInFront": SpawnPedestrianInFront,
        # "SpawnActorInFront": SpawnActorInFront,
        
        # For Regression
        "Regression": Regression,

        "CutInRoute": CutInRoute
    }

    @classmethod
    def get_weather_scenarios(cls):
        return cls.WEATHER_SCENARIOS

    @classmethod
    def get_time_scenarios(cls):
        return cls.TIME_SCENARIOS

    @classmethod
    def get_other_scenarios(cls):
        return cls.OTHER_SCENARIOS

    @classmethod
    def get_background_scenarios(cls):
        return cls.BACKGROUND_SCENARIOS

    @classmethod
    def get_all_scenarios(cls):
        all_scenarios = dict()
        all_scenarios.update(cls.get_weather_scenarios())
        all_scenarios.update(cls.get_time_scenarios())
        all_scenarios.update(cls.get_background_scenarios())
        all_scenarios.update(cls.get_other_scenarios())
        return all_scenarios
