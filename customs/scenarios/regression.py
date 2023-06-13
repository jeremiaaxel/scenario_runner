import carla
import math

from py_trees.composites import Sequence, Parallel
from py_trees.common import ParallelPolicy
from customs.helpers.blueprints import get_heading, hide_actors

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorDestroy, ActorTransformSetter
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToLocationAlongRoute
from srunner.scenariomanager.timer import TimeOut
from srunner.scenarios.basic_scenario import BasicScenario


class Regression(BasicScenario):
    delta_ys = [num for num in range(5, 36, 5)]
    delta_xs = [num for num in range(-15, 16, 5)]
    transforms = []
    actor_timeout = 15 # (s)
    timeout = -1

    model = "walker.*"

    def __init__(self, 
                 world,
                 ego_vehicles,
                 config,
                 debug_mode=False, 
                 terminate_on_failure=False, 
                 timeout=60,
                 criteria_enable=False):

        self.timeout = timeout
        self._trigger_wp = config.trigger_points[0]
        self._ego_route = CarlaDataProvider.get_ego_vehicle_route()
        print(f"Trigger point {self._trigger_wp}")
        super().__init__("Regression", 
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

        ego_heading = self._trigger_wp.rotation.yaw
        ego_location = self._trigger_wp.location

        for delta_y_rel in self.delta_ys:
            actor_location = ego_location
            delta_x, delta_y = delta_relative_to_absolute(ego_heading, 
                                                           0,
                                                           delta_y_rel)
            actor_location.y += delta_y
            actor_location.x += delta_x
            actor_location.z += 0.2
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
            root.add_child(ActorTransformSetter(actor, self.transforms[actor_idx]))
            root.add_child(TimeOut(self.actor_timeout))
            root.add_child(ActorDestroy(actor, name=f"Destroy actor {actor.id}"))

        return root
