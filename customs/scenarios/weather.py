from __future__ import print_function

import carla
import py_trees
import logging

from enum import Enum
from typing import Union
from customs.behaviors.change_weather_parameter_only import ChangeWeatherParameterOnly

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeWeather, ChangeRoadFriction
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenariomanager.weather_sim import Weather

logger = logging.getLogger(__name__)
class RoadFriction(Enum):
    # WARNING: THE VALUE IS WRONG FOR CARLA
    """
    http://hyperphysics.phy-astr.gsu.edu/hbase/Mechanics/frictire.html
    tldr:
        - dry: 0.7
        - wet: 0.4
    """
    DRY = 0.7
    WET = 0.4
    DEFAULT = 10.0


class WeatherBasicRoute(BasicScenario):
    """
    To make scenario changing weather/time, specify properties on weather_config dictionary:
    https://carla.readthedocs.io/en/0.9.12/python_api/#carlaweatherparameters
    """
    weather_config: dict = {}

    def __init__(self, world, ego_vehicles, config, debug_mode=False, criteria_enable=True,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario
        """
        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        self.timeout = timeout # timeout of scenario in seconds
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        self._world = CarlaDataProvider.get_world()
        super(WeatherBasicRoute, self).__init__("WeatherBasicRoute",
                                                  ego_vehicles,
                                                  config,
                                                  world,
                                                  debug_mode,
                                                  criteria_enable=criteria_enable)

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []
        collision_criterion = CollisionTest(self.ego_vehicles[0])

        criteria.append(collision_criterion)
        return criteria
    
    def _weather(self):
        weather = self._world.get_weather()
        # logger.debug_s(f"Modified weather params: \n {'\n'.join(self.__class__.weather_config.items())}")
        logger.debug_s(self.__class__.weather_config.items())
        logger.debug_s(f"Previous weather: {weather}")
        for property, value in self.__class__.weather_config.items():
            setattr(weather, property, value)
        logger.debug_s(f"New weather: {weather}")
        return Weather(weather)
    
    def _road_friction(self) -> Union[RoadFriction, float]:
        return RoadFriction.DEFAULT
        
    def _create_behavior(self):
        behavior = py_trees.composites.Sequence(name=__class__.__name__)
        change_weather = py_trees.meta.oneshot(ChangeWeatherParameterOnly)(self.__class__.weather_config)
        # change_weather = py_trees.meta.oneshot(ChangeWeather)(self._weather())
        behavior.add_child(change_weather)
        
        # change_road_friction = py_trees.meta.oneshot(ChangeRoadFriction)(self._road_friction())
        # behavior.add_child(change_road_friction)
        return behavior
    
    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()

class WeatherClear(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 10.0,
        'precipitation': 0.0,
        'precipitation_deposits': 0.0,
        'wind_intensity': 5.0,
        'fog_density': 0.0,
        'fog_distance': 0.0,
        'fog_falloff': 0.2,
        'wetness': 0.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.0,
        'mie_scattering_scale': 0.0331,
    }

class WeatherOvercast(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 80.0,
        'precipitation': 0.0,
        'precipitation_deposits': 0.0,
        'wind_intensity': 50.0,
        'fog_density': 2.0,
        'fog_distance': 0.75,
        'fog_falloff': 0.1,
        'wetness': 10.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.3,
        'mie_scattering_scale': 0.0331,
    }

class WeatherHardRain(WeatherBasicRoute):
    weather_config = {
        'cloudiness': 100.0,
        'precipitation': 80.0,
        'precipitation_deposits': 90.0,
        'wind_intensity': 100.0,
        'fog_density': 7.0,
        'fog_distance': 0.75,
        'fog_falloff': 0.1,
        'wetness': 100.0,
        'scattering_intensity': 0.0,
        'mie_scattering_scale': 0.3,
        'mie_scattering_scale': 0.0331,
    }


## ---------- PRESETS --------- ##
class WeatherClearSunsetRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "ClearSunset")
        return Weather(weather)

class WeatherHardRainNightRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "HardRainNight")
        return Weather(weather)

class WeatherMidRainyNoonRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "MidRainyNoon")
        return Weather(weather)

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

class WeatherWetNoonRoute(WeatherBasicRoute):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def _weather(self):
        weather = getattr(carla.WeatherParameters, "WetNoon")
        return Weather(weather)
## ---------- END OF PRESETS --------- ##
