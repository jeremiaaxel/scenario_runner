from customs.scenarios.obstructing_actor import (
    ObstructingVehicleHorn, ObstructingVehicleTimer,
    ObstructingPedestrianHorn, ObstructingPedestrianTimer
)
from customs.scenarios.pedestrian_crossing import PedestrianCyclistCrossing, PedestrianCyclistProps, pedestrian_crossing_wrapper
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

class AvailableScenarios(object): 
    WEATHER_SCENARIOS = {
        # "WetNoon": WeatherWetNoonRoute,
        # "MidRainyNoon": WeatherMidRainyNoonRoute,
        # "HardRainNight": WeatherHardRainNightRoute,
        # "ClearSunset": WeatherClearSunsetRoute,
        # "WeatherRainyDay": WeatherRainyDayRoute,
        
        "Clear": get_weather_scenario('clear'),
        "HardRain": get_weather_scenario('hardrain'),
        "Overcast": get_weather_scenario('overcast'),
        "Foggy": get_weather_scenario('foggy'),
        "LightFoggy": get_weather_scenario('lightfoggy')
    }

    TIME_SCENARIOS = {
        "Night": TimeNight,
        "Day": TimeDay,
        "Sunrise": TimeSunrise,
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
        "PedestrianFarCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianFarCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "PedestrianCloseCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianCloseCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "CyclistFarCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing,
                                                          custom_name="CyclistFarCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
        "CyclistCloseCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing,
                                                          custom_name="CyclistCloseCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_NORMAL),
                                                          
        "PedestrianSlowFarCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianSlowFarCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "PedestrianSlowCloseCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing, 
                                                          custom_name="PedestrianSlowCloseCrossing",
                                                          adversary_type=False,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_CLOSE,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "CyclistSlowFarCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing,
                                                          custom_name="CyclistSlowFarCrossing",
                                                          adversary_type=True,
                                                          _start_distance=PedestrianCyclistProps.DISTANCE_FAR,
                                                          custom_speed=PedestrianCyclistProps.SPEED_SLOW),
        "CyclistSlowCloseCrossing": pedestrian_crossing_wrapper(PedestrianCyclistCrossing,
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
