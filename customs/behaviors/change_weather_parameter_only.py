import py_trees

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import AtomicBehavior
from srunner.scenariomanager.weather_sim import Weather


class ChangeWeatherParameterOnly(AtomicBehavior):
    def __init__(self, weather_config, name="ChangeWeather"):
        """
        Setup parameters
        """
        super(ChangeWeatherParameterOnly, self).__init__(name)
        self._weather_config = weather_config

    def update(self):
        """
        Write weather into blackboard and exit with success

        returns:
            py_trees.common.Status.SUCCESS
        """
        weather = CarlaDataProvider.get_world().get_weather()

        for property, value in self._weather_config.items():
            setattr(weather, property, value)

        self._weather = Weather(weather)

        py_trees.blackboard.Blackboard().set("CarlaWeather", self._weather, overwrite=True)
        return py_trees.common.Status.SUCCESS
