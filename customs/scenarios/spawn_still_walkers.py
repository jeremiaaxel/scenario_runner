import carla
import math

from py_trees.composites import Sequence
from customs.helpers.blueprints import hide_actors

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorDestroy, ActorTransformSetter
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToLocationAlongRoute
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario


class RegressionScenarios(BasicScenario):
    """
    Spawn some walkers in certain x and y distances overtime.
    """
    # delta_ys = [num for num in range(5, 36, 5)]
    # delta_xs = [num for num in range(-5, 11, 5)]

    delta_ys = [35]
    delta_xs = [0]
    transforms = []
    actor_timeout = 15 # (s)

    model = "walker.pedestrian.0001"
    model = "vehicle.carlamotors.carlacola"
    # model = "vehicle.micro.microlino"
    # model = "vehicle.vespa.zx125"
    # model = "vehicle.bh.crossbike"

    def __init__(self, 
                 world,
                 ego_vehicles,
                 config,
                 debug_mode=False, 
                 terminate_on_failure=False, 
                 timeout=60,
                 criteria_enable=False):

        self.timeout = timeout
        print(f"{config.trigger_points[0]}")
        self._trigger_wp = CarlaDataProvider.get_map().get_waypoint(config.trigger_points[0].location)
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        super().__init__("SpawnStillWalkers", 
                         ego_vehicles, 
                         config, 
                         world, 
                         debug_mode, 
                         terminate_on_failure, 
                         criteria_enable)

    def _spawn_actors(self, config):
        def delta_relative_to_absolute(compass, delta_x, delta_y):
            delta_x, delta_y = delta_y, delta_x
            rad = math.radians(compass)
            x = delta_x * math.cos(rad) + delta_y * math.sin(rad)
            y = -1 * delta_x * math.sin(rad) + delta_y * math.cos(rad)
            return (x, y)

        ego_heading = self._trigger_wp.transform.rotation.yaw
        ego_location = self._trigger_wp.transform.location
        buffer = 5

        for delta_y_rel in self.delta_ys:
            for delta_x_rel in self.delta_xs:
                actor_location = carla.Location(ego_location)
                delta_x, delta_y = delta_relative_to_absolute(ego_heading, 
                                                            delta_x_rel,
                                                            delta_y_rel + buffer)
                actor_location.y += delta_y
                actor_location.x += delta_x
                actor_location.z += 0.8
                actor_transform = carla.Transform(actor_location, 
                                                carla.Rotation())
                actor = CarlaDataProvider.request_new_actor(self.model,
                                                            actor_transform,
                                                            actor_category="pedestrian")
                if actor is None:
                    print(f"Failed to spawn actor on delta y: {delta_y_rel}")
                else:
                    self.other_actors.append(actor)
                    self.transforms.append(actor_transform)

    def _post_initialize_actors(self):
        hide_actors(self.other_actors)

    def _initialize_actors(self, config):
        self._spawn_actors(config)
        self._post_initialize_actors()

    def _create_behavior(self):
        """
        Sets one pedestrian at a time with different distance from the ego vehicle
        """
        root = Sequence(name=self.__class__.__name__)

        for actor_idx, actor in enumerate(self.other_actors):
            actor_seq = Sequence(name="Actor sequence")
            actor_seq.add_child(ActorTransformSetter(actor, self.transforms[actor_idx]))
            # actor_seq.add_child(TimeOut(self.actor_timeout))
            # actor_seq.add_child(ActorDestroy(actor, name=f"Destroy actor {actor.id}"))
            root.add_child(actor_seq)

        return root

    def _create_test_criteria(self):
        pass