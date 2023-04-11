from __future__ import print_function
from typing import Union

import carla

from srunner.scenariomanager.weather_sim import Weather
from customs.scenarios.WeatherBasic import RoadFriction, WeatherBasicRoute

class WeatherRainyDayRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = carla.WeatherParameters(
            cloudiness=8.0, 
            precipitation=80.0, precipitation_deposits=60.0,
            wetness=78.0,
            sun_altitude_angle=81.7,
            sun_azimuth_angle=1.9
        )
        return Weather(weather)
    
    def _road_friction(self) -> Union[RoadFriction, float]:
        return 10.0
