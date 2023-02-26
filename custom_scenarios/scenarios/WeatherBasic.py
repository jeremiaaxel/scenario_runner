from __future__ import print_function

import py_trees

import carla
import re

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ChangeWeather, ChangeRoadFriction
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenariomanager.weather_sim import Weather

class WeatherBasicRoute(BasicScenario):
    """
    This class holds everything required for a simple weather change:
        clear, cloudy, raining
    """
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=60):
        """
        Setup all relevant parameters and create scenario
        """

        self._wmap = CarlaDataProvider.get_map()
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location
        # Timeout of scenario in seconds
        self.timeout = timeout

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
    
    def _create_behavior(self):
        behavior = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name="WeatherChange")
        env_behavior = self._create_environment_behavior()
        behavior.add_child(env_behavior)
        return behavior
    
    def _create_environment_behavior(self):
        # Set the appropriate weather conditions

        env_behavior = py_trees.composites.Parallel(
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL, name="EnvironmentBehavior")

        weather_update = ChangeWeather(self._weather())
        env_behavior.add_child(weather_update)
        # road_friction = ChangeRoadFriction(self._road_friction())
        # env_behavior.add_child(oneshot_with_check(variable_name="InitRoadFriction", behaviour=road_friction))

        return env_behavior
    
    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()