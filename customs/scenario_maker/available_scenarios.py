from customs.scenarios.obstructing_vehicle import ObstructingVehicle
from customs.scenarios.pedestrian_crossing import CyclistCrossing, CyclistSlowCrossing, PedestrianCrossing, PedestrianWalkCrossing
from customs.scenarios.spawn_angkot import SpawnAngkot, SpawnAngkotOnTrigger
from customs.scenarios.spawn_bike import SpawnBike, SpawnBikeOnTrigger
from customs.scenarios.spawn_pedestrian import SpawnPedestrian, SpawnPedestrianOnTrigger
from customs.scenarios.time import TimeDay, TimeNight, TimeSunrise
from customs.scenarios.weather import (
    WeatherClear, WeatherHardRain, WeatherOvercast,
    # Presets
    WeatherClearSunsetRoute, WeatherWetNoonRoute, 
    WeatherHardRainNightRoute, WeatherRainyDayRoute, 
    WeatherMidRainyNoonRoute
)
from customs.scenarios.cut_in import CutInRoute

class AvailableScenarios(object):
    WEATHER_SCENARIOS = {
        # "WetNoon": WeatherWetNoonRoute,
        # "MidRainyNoon": WeatherMidRainyNoonRoute,
        # "HardRainNight": WeatherHardRainNightRoute,
        # "ClearSunset": WeatherClearSunsetRoute,
        # "WeatherRainyDay": WeatherRainyDayRoute,
        
        "Clear": WeatherClear,
        "HardRain": WeatherHardRain,
        "Overcast": WeatherOvercast
    }

    TIME_SCENARIOS = {
        "Night": TimeNight,
        "Day": TimeDay,
        "Sunrise": TimeSunrise,
    }

    OTHER_SCENARIOS = {
        # Spawning(s)
        "SpawnAngkot": SpawnAngkot,
        "SpawnAngkotOnTrigger": SpawnAngkotOnTrigger,
        "SpawnBike": SpawnBike,
        "SpawnBikeOnTrigger": SpawnBikeOnTrigger,
        "SpawnPedestrian": SpawnPedestrian,
        "SpawnPedestrianOnTrigger": SpawnPedestrianOnTrigger,

        # Crossings(s)
        "PedestrianCrossing": PedestrianCrossing,
        "PedestrianWalkCrossing": PedestrianWalkCrossing,
        "CyclistCrossing": CyclistCrossing,
        "CyclistSlowCrossing": CyclistSlowCrossing,

        # Obstructing(s)
        "ObstructingVehicle": ObstructingVehicle,

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
    def get_all_scenarios(cls):
        all_scenarios = dict()
        all_scenarios.update(cls.get_weather_scenarios())
        all_scenarios.update(cls.get_time_scenarios())
        all_scenarios.update(cls.get_other_scenarios())
        return all_scenarios