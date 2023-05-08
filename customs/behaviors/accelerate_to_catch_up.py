import math
import carla
import py_trees
import operator

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import AccelerateToCatchUp, WaypointFollower, get_actor_control
from srunner.tools.scenario_helper import detect_lane_obstacle


class AccelerateToCatchUpFollowWaypoint(WaypointFollower):
    def __init__(self, 
                 actor, 
                 other_actor,
                 throttle_value=1,
                 delta_velocity=0,
                 trigger_distance=5,
                 max_distance=500,
                 name="AccelerateToCatchUpFollowWaypoints"):
        super().__init__(actor, None, None, None, False, name)
        self._other_actor = other_actor
        self._throttle_value = throttle_value
        self._delta_velocity = delta_velocity  # 1m/s=3.6km/h
        self._trigger_distance = trigger_distance
        self._max_distance = max_distance

        self._control, self._type = get_actor_control(actor)

        self._initial_actor_pos = None

    def initialise(self):
        super().initialise()
        self._initial_actor_pos = CarlaDataProvider.get_location(self._actor)

    def update(self):
        new_status = py_trees.common.Status.RUNNING

        check_term = operator.attrgetter("terminate_WF_actor_{}".format(self._actor.id))
        terminate_wf = check_term(py_trees.blackboard.Blackboard())

        check_run = operator.attrgetter("running_WF_actor_{}".format(self._actor.id))
        active_wf = check_run(py_trees.blackboard.Blackboard())

        # Termination of WF if the WFs unique_id is listed in terminate_wf
        # only one WF should be active, therefore all previous WF have to be terminated
        if self._unique_id in terminate_wf:
            terminate_wf.remove(self._unique_id)
            if self._unique_id in active_wf:
                active_wf.remove(self._unique_id)

            py_trees.blackboard.Blackboard().set(
                "terminate_WF_actor_{}".format(self._actor.id), terminate_wf, overwrite=True)
            py_trees.blackboard.Blackboard().set(
                "running_WF_actor_{}".format(self._actor.id), active_wf, overwrite=True)
            new_status = py_trees.common.Status.SUCCESS
            return new_status

        if self._blackboard_queue_name is not None:
            while not self._queue.empty():
                actor = self._queue.get()
                if actor is not None and actor not in self._actor_dict:
                    self._apply_local_planner(actor)

        success = True
        for actor in self._local_planner_dict:
            local_planner = self._local_planner_dict[actor] if actor else None
            if actor is not None and actor.is_alive and local_planner is not None:

                # Check if the actor is a vehicle/bike
                if not isinstance(actor, carla.Walker):
                    control = local_planner.run_step(debug=False)

                    ## ACCELERATE
                    # get actor speed
                    actor_speed = CarlaDataProvider.get_velocity(actor)
                    target_speed = CarlaDataProvider.get_velocity(self._other_actor) + self._delta_velocity

                    # distance between actors
                    distance = CarlaDataProvider.get_location(actor).distance(
                        CarlaDataProvider.get_location(self._other_actor))

                    # driven distance of actor
                    driven_distance = CarlaDataProvider.get_location(actor).distance(self._initial_actor_pos)
                    
                    self._target_speed = target_speed
                    if actor_speed < target_speed:
                        # set throttle to throttle_value to accelerate
                        control.throttle = self._throttle_value

                    if actor_speed >= target_speed:
                        # keep velocity until the actors are in trigger distance
                        control.throttle = 0
                    ## ----------

                    if self._avoid_collision and detect_lane_obstacle(actor):
                        control.throttle = 0.0
                        control.brake = 1.0

                    # actor.apply_control(control)
                    self._actor.apply_control(control)
                    print(control)
                    print(CarlaDataProvider.get_velocity(actor))

                    # new status:
                    if distance <= self._trigger_distance:
                        success = True
                    elif driven_distance > self._max_distance:
                        return py_trees.common.Status.FAILURE
                    else:
                        success = False

                    # Check if the actor reached the end of the plan
                    # @TODO replace access to private _waypoints_queue with public getter
                    if local_planner._waypoints_queue:  # pylint: disable=protected-access
                        success = False
                # If the actor is a pedestrian, we have to use the WalkerAIController
                # The walker is sent to the next waypoint in its plan
                else:
                    actor_location = CarlaDataProvider.get_location(actor)
                    success = False
                    if self._actor_dict[actor]:
                        location = self._actor_dict[actor][0]
                        direction = location - actor_location
                        direction_norm = math.sqrt(direction.x**2 + direction.y**2)
                        control = actor.get_control()
                        control.speed = self._target_speed
                        control.direction = direction / direction_norm
                        actor.apply_control(control)
                        if direction_norm < 1.0:
                            self._actor_dict[actor] = self._actor_dict[actor][1:]
                            if self._actor_dict[actor] is None:
                                success = True
                    else:
                        control = actor.get_control()
                        control.speed = self._target_speed
                        control.direction = CarlaDataProvider.get_transform(actor).rotation.get_forward_vector()
                        actor.apply_control(control)

        if success:
            new_status = py_trees.common.Status.SUCCESS

        return new_status
