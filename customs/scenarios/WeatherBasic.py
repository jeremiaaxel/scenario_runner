from __future__ import print_function
from typing import Union

import carla
import py_trees

from enum import Enum
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeWeather, ChangeRoadFriction
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenariomanager.weather_sim import Weather

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
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
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
        weather = carla.WeatherParameters()
        weather.precipitation = 0.0
        weather.wetness = 0.0
        weather.cloudiness = 0.0
        return Weather(weather)
    
    def _road_friction(self) -> Union[RoadFriction, float]:
        return RoadFriction.DEFAULT
        
    def _create_behavior(self):
        behavior = py_trees.composites.Sequence(name="WeatherChange")
        change_weather = py_trees.meta.oneshot(ChangeWeather)(self._weather())
        change_road_friction = py_trees.meta.oneshot(ChangeRoadFriction)(self._road_friction())
        behavior.add_children([change_weather, change_road_friction])
        return behavior
    
    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()