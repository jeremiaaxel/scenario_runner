from customs.scenarios.SpawnAngkot import SpawnAngkotOnTrigger
from customs.scenarios.SpawnBike import SpawnBikeOnTrigger
from customs.scenarios.SpawnPedestrian import SpawnPedestrianOnTrigger
from customs.scenarios.WeatherClearSunset import WeatherClearSunsetRoute
from customs.scenarios.WeatherHardRainNight import WeatherHardRainNightRoute
from customs.scenarios.WeatherMidRainyNoon import WeatherMidRainyNoonRoute
from customs.scenarios.WeatherRainyDay import WeatherRainyDayRoute
from customs.scenarios.WeatherWetNoon import WeatherWetNoonRoute
from srunner.scenarios.object_crash_vehicle import DynamicObjectCrossing


class AvailableScenarios(object):
    WEATHER_SCENARIOS = {
        "WetNoon": WeatherWetNoonRoute,
        "MidRainyNoon": WeatherMidRainyNoonRoute,
        "HardRainNight": WeatherHardRainNightRoute,
        "ClearSunset": WeatherClearSunsetRoute,
        "WeatherRainyDay": WeatherRainyDayRoute,
    }

    TIME_SCENARIOS = {
    }

    OTHER_SCENARIOS = {
        "SpawnAngkotOnTrigger": SpawnAngkotOnTrigger,
        "SpawnBikeOnTrigger": SpawnBikeOnTrigger,
        "SpawnPedestrianOnTrigger": SpawnPedestrianOnTrigger,
        "PedestrianCrossing": DynamicObjectCrossing,
    }

    @staticmethod
    def get_weather_scenarios():
        return __class__.WEATHER_SCENARIOS

    @staticmethod
    def get_time_scenarios():
        return __class__.TIME_SCENARIOS

    @staticmethod
    def get_other_scenarios():
        return __class__.OTHER_SCENARIOS

    @staticmethod
    def get_all_scenarios():
        all_scenarios = dict()
        all_scenarios.update(__class__.get_weather_scenarios())
        all_scenarios.update(__class__.get_time_scenarios())
        all_scenarios.update(__class__.get_other_scenarios())
        return all_scenarios