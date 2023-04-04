
import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


class JunctionCrossingVehiclePass(BasicScenario):
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=180):
        """
        Setup all relevant parameters and create scenario
        and instantiate scenario manager
        """
        # Timeout of scenario in seconds
        self.timeout = timeout
        self.subtype = config.subtype
        self._reference_waypoint = self._wmap.get_waypoint(config.trigger_points[0].location)
        self._trigger_location = config.trigger_points[0].location

        super(JunctionCrossingVehiclePass, self).__init__("JunctionCrossingVehiclePass",
                                                          ego_vehicles,
                                                          config,
                                                          world,
                                                          debug_mode,
                                                          criteria_enable=criteria_enable)
        
    def _initialize_actors(self, config):
        """
        trigger location is on junction
        Spawn actor that passes junction at the same time with ego vehicle
        """
        self.other_vehicles = CarlaDataProvider.request_new_actor('vehicle.tesla.cybertruck',
                                                                  self._trigger_location)

