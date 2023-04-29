from customs.scenarios.SpawnAngkot import SpawnAngkotOnTrigger
from customs.scenarios.SpawnBike import SpawnBikeOnTrigger
from customs.scenarios.SpawnPedestrian import SpawnPedestrianOnTrigger
from customs.scenarios.Time import TimeDay, TimeNight, TimeSunrise

from customs.scenarios.Weather import (
    WeatherClear, WeatherHardRain, WeatherOvercast,
    # Presets
    WeatherClearSunsetRoute, WeatherWetNoonRoute, WeatherHardRainNightRoute, WeatherRainyDayRoute, WeatherMidRainyNoonRoute
)
from srunner.scenarios.object_crash_vehicle import DynamicObjectCrossing


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
        "SpawnAngkotOnTrigger": SpawnAngkotOnTrigger,
        "SpawnBikeOnTrigger": SpawnBikeOnTrigger,
        "SpawnPedestrianOnTrigger": SpawnPedestrianOnTrigger,
        "PedestrianCrossing": DynamicObjectCrossing,
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
