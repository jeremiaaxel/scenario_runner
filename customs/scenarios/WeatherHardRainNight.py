from __future__ import print_function

import carla

from srunner.scenariomanager.weather_sim import Weather
from customs.scenarios.WeatherBasic import WeatherBasicRoute

class WeatherHardRainNightRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "HardRainNight")
        # weather = carla.WeatherParameters(
        #     cloudiness=78.0, 
        #     precipitation=80.0, precipitation_deposits=60.0,
        #     wetness=78.0,
        #     sun_altitude_angle=-90.0
        # )
        return Weather(weather)
