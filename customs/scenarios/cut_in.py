import logging
import py_trees
import carla
from customs.behaviors.accelerate_to_catch_up_follow_waypoint import AccelerateToCatchUpFollowWaypoint
from customs.helpers.blueprints import freeze_vehicle

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorTransformSetter, LaneChange, WaypointFollower
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance, InTriggerDistanceToVehicle
from srunner.scenarios.cut_in import CutIn

default_model_name = "vehicle.tesla.model3"

logger = logging.getLogger(__name__)


class CutInRoute(CutIn): 
    _transforms_visible = []

    offset = {
        "behind_ego": 20,
        "behind_cutter": 10,
        "underground": 500 
    }

    def __init__(self, 
                 world, 
                 ego_vehicles, 
                 config, randomize=False, 
                 debug_mode=False, 
                 criteria_enable=True, 
                 timeout=600, 
                 spawn_straight_other=True):
        self._spawn_straight_other = spawn_straight_other
        super().__init__(world, 
                         ego_vehicles, 
                         config, 
                         randomize, 
                         debug_mode, 
                         criteria_enable, 
                         timeout)

    def _initialize_actors(self, config):
        """
        Spawn cutter vehicle on the lane right next to the trigger point.
        Spawn straight vehicle right behind the cutter vehicle.
        """

        cutter_model_name = default_model_name

        wp_trigger = self._reference_waypoint

        # get right lane of the ego vehicle, or left lane
        wp_spawn_cutter = wp_trigger.get_right_lane()
        self._direction = "left"
        if wp_spawn_cutter is None:
            wp_spawn_cutter = wp_trigger.get_left_lane()
            self._direction = "right"
        if wp_spawn_cutter is None:
            logger.warn(f"Spawn waypoint is None, maybe {wp_trigger.transform.location} a single lane?")
            logger.warn(f"Spawning directly behind ego vehicle, but may not be able to do cut in due to single lane road")
            wp_spawn_cutter = wp_trigger
            self._direction = None

        logger.debug_s(f"Lane change direction: {self._direction}")
        # find waypoint behind ego vehicle
        logger.debug_s(f"Trigger waypoint: {wp_trigger}")
        wp_spawn_cutter = wp_spawn_cutter.previous(self.offset.get('behind_ego'))
        if isinstance(wp_spawn_cutter, list):
            if len(wp_spawn_cutter) > 1:
                logger.debug_s(f"Waypoint detected is more than one, selected the last in the list; may select the undesired waypoint")
            wp_spawn_cutter = wp_spawn_cutter[-1]
        logger.debug_s(f"Cutter's spawning waypoint: {wp_spawn_cutter}")

        if self._spawn_straight_other:
            wp_spawn_straight = wp_spawn_cutter.previous(self.offset.get('behind_cutter'))
            if isinstance(wp_spawn_straight, list):
                if len(wp_spawn_straight) > 1:
                    logger.debug_s(f"Waypoint detected is more than one, selected the last in the list; may select the undesired waypoint")
                wp_spawn_straight = wp_spawn_straight[-1]
            logger.debug_s(f"Straight's spawning waypoint: {wp_spawn_straight}")

        # spawn cutter and straight vehicle(s)
        cutter_transform = carla.Transform(
            carla.Location(wp_spawn_cutter.transform.location.x,
                           wp_spawn_cutter.transform.location.y,
                           wp_spawn_cutter.transform.location.z - self.offset.get("underground")),
            wp_spawn_cutter.transform.rotation)
        self._transforms_visible.append(wp_spawn_cutter.transform)

        if self._spawn_straight_other:
            straight_transform = carla.Transform(
                carla.Location(wp_spawn_straight.transform.location.x,
                            wp_spawn_straight.transform.location.y,
                            wp_spawn_straight.transform.location.z - self.offset.get("underground")),
                wp_spawn_straight.transform.rotation)
            self._transforms_visible.append(wp_spawn_straight.transform)

        cutter_vehicle = CarlaDataProvider.request_new_actor(cutter_model_name, cutter_transform)
        if cutter_vehicle is None:
            raise RuntimeError("Failed to spawn cutter vehicle")
        freeze_vehicle(cutter_vehicle)
        self.other_actors.append(cutter_vehicle)

        if self._spawn_straight_other:
            straight_vehicle = CarlaDataProvider.request_new_actor(cutter_model_name, straight_transform)
            if straight_vehicle is None:
                raise RuntimeError("Failed to spawn straight vehicle")
            freeze_vehicle(straight_vehicle)
            self.other_actors.append(straight_vehicle)


    def _create_behavior(self):
        """
        Order of sequence:
        - car_visible: spawn car at a visible transform
        - just_drive: drive until in trigger distance to ego_vehicle
        - accelerate: accelerate to catch up distance to ego_vehicle
        - lane_change: change the lane
        - endcondition: drive for a defined distance
        """

        # car_visible
        vehicles_behavior = py_trees.composites.Parallel("VehiclesBehavior", 
                                                         policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        cutter_behavior = py_trees.composites.Sequence("CarOn_{}_Lane" .format(self._direction))
        straight_behavior = py_trees.composites.Sequence("CarOn_{}_Lane_straight" .format(self._direction))

        # behaviour = py_trees.composites.Sequence("CarOn_{}_Lane" .format(self._direction))
        cutter_visible = ActorTransformSetter(self.other_actors[0], 
                                              self._transforms_visible[0],
                                              physics=True)
        cutter_behavior.add_child(cutter_visible)

        # just_drive
        just_drive = py_trees.composites.Parallel("DrivingStraight", 
                                                  policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)

        car_driving = WaypointFollower(self.other_actors[0], self._velocity)
        just_drive.add_child(car_driving)

        trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], 
                                                      self.ego_vehicles[0], 
                                                      self._trigger_distance)
        just_drive.add_child(trigger_distance)
        cutter_behavior.add_child(just_drive)

        # accelerate
        accelerate = AccelerateToCatchUpFollowWaypoint(self.other_actors[0], 
                                                       self.ego_vehicles[0], 
                                                       throttle_value=1,
                                                       delta_velocity=self._delta_velocity, 
                                                       trigger_distance=5, 
                                                       max_distance=500,
                                                       avoid_collision=True)
        cutter_behavior.add_child(accelerate)

        # lane_change
        lane_change = LaneChange(self.other_actors[0], 
                                 speed=None, 
                                 direction=self._direction, 
                                 distance_same_lane=5, 
                                 distance_other_lane=100)
        cutter_behavior.add_child(lane_change)
        
        if self._spawn_straight_other:
            # straight vehicle will only spawn and then follow waypoint
            straight_visible = ActorTransformSetter(self.other_actors[1], 
                                                    self._transforms_visible[1],
                                                    physics=True)
            straight_behavior.add_child(straight_visible)
            straight_driving = WaypointFollower(self.other_actors[1], 
                                                self._velocity,
                                                avoid_collision=True)
            straight_behavior.add_child(straight_driving)

        vehicles_behavior.add_child(cutter_behavior)
        vehicles_behavior.add_child(straight_behavior)

        # endcondition
        endcondition = DriveDistance(self.other_actors[0], 200)

        # build tree
        root = py_trees.composites.Sequence("Behavior", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ONE)
        root.add_child(vehicles_behavior)
        root.add_child(endcondition)
        return root