from __future__ import print_function

import math
import py_trees

import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                      ActorDestroy,
                                                                      KeepVelocity,
                                                                      HandBrakeVehicle)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest


from custom_scenarios.scenarios.WeatherBasic import WeatherBasicRoute
from srunner.scenariomanager.weather_sim import Weather

class WeatherWetNoonRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "WetNoon")
        # weather = carla.WeatherParameters(
        #     cloudiness=78.0, 
        #     precipitation=80.0, precipitation_deposits=60.0,
        #     wetness=78.0,
        #     sun_altitude_angle=-90.0
        # )
        return Weather(weather)
