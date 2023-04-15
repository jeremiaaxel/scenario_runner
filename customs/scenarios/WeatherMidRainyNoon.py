from __future__ import print_function

import carla

from srunner.scenariomanager.weather_sim import Weather
from customs.scenarios.WeatherBasic import WeatherBasicRoute

class WeatherMidRainyNoonRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "MidRainyNoon")
        return Weather(weather)
