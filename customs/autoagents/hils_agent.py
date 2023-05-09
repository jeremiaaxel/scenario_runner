#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle
via keyboard. Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function
from typing import Callable, Tuple
import zmq
import os
from hils_connector.carla_handlers.outbound import (
    GnssHandler,
    LidarHandler,
    CameraHandler,
)
from hils_connector.carla_handlers.inbound import ControlHandler
# from hils_connector.dm import Controller2D, LocMap
from threading import Event
from carla import VehicleControl
import logging

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from customs.autoagents.human_tram_agent import HumanTramAgent

# has to append PYTHONPATH with $HOME/Documents/khansa/rilis3
from controller2d import Controller2D
from lokalisasi import LocMap


class Integer:
    def __init__(self, value: int):
        self.val = value


class HilsAgent(HumanTramAgent):
    """
    Human tram agent to control the ego vehicle via ZMQ
    """

    agent_engaged = False
    prev_timestamp = 0
    ego_vehicle = None

    _log = logging.getLogger("HILS agent")

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)

        self._vehicle_control_event = Event()

        self._dm_command = Integer(0)

        self._setup_sensors()

        self._is_first_run = True

    def _setup_sensors(self):
        print("setup sensors called")
        zmq_context = zmq.Context()
        zmq_host = os.getenv("ZMQ_HOST", "*")

        for sensor in self.sensors():
            if sensor["type"] == "sensor.camera.rgb":
                port = os.getenv("ZMQ_CAMERA_PORT", 5555)
                self._camera_handler = CameraHandler(zmq_host, port, zmq_context)
            elif sensor["type"] == "sensor.lidar.ray_cast":
                port = os.getenv("ZMQ_LIDAR_PORT", 5558)
                self._lidar_handler = LidarHandler(zmq_host, port, zmq_context)
            elif sensor["type"] == "sensor.other.gnss":
                port = os.getenv("ZMQ_GNSS_PORT", 5557)
                self._gnss_handler = GnssHandler(zmq_host, port, zmq_context)
            else:
                self._log.warn("Sensor of type %s is not supported. Will be ignored.", sensor["type"])
                continue
                # raise TypeError("Invalid sensor type: {}".format(sensor["type"]))

        zmq_host = os.getenv("ZMQ_SRC", "167.205.66.15")
        port = os.getenv("ZMQ_CONTROL_PORT", 5556)
        self._control_receiver = ControlHandler(
            zmq_host, port, self._on_vehicle_control, zmq_context
        )

    def _setup_dm(self):
        """
        setup helper
        """
        carla_map = CarlaDataProvider.get_map()
        # set_egovehicle is called before run_step which calls _setup_dm
        route = CarlaDataProvider.get_ego_vehicle_route()

        dt = 1.0 / 20.0
        args_lateral_dict = {"K_P": 1.02, "K_I": 0.001, "K_D": 0.2, "dt": dt}
        args_longitudinal_dict = {"K_P": 5, "K_I": 0.3, "K_D": 0.13, "dt": dt}

        self._locmap = LocMap(carla_map, self.ego_vehicle)
        self._locmap.set_destination(
            start_location=route[0][0],
            end_location=route[-1][0],
        )

        self._dm_controller = Controller2D(
            self.ego_vehicle,
            carla_map,
            self._locmap.wpt,
            self._locmap.lateral_route,
            args_lateral_dict,
            args_longitudinal_dict,
        )


    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        Steering: NPC agent
        Acceleration: From ZMQ

        Overriden controls by keyboards:
          - throttle
          - brake
          - hand_brake
        """
        if self._is_first_run:
            self._is_first_run = False
            self._setup_dm()
            # immediately return because no control yet
            # AV is stopped at first run
            return VehicleControl(
                throttle=0,
                steer=0,
                brake=1,
                hand_brake=True,
                manual_gear_shift=False,
            )

        self._vehicle_control_event.wait()

        throttle, _, brake = self._translate_dm_command(timestamp)

        # steering: from NPC agent
        control_super = super().run_step(input_data, timestamp)

        control = VehicleControl(
            throttle=throttle,
            steer=control_super.steer,
            #steer=steer,
            brake=brake,
            hand_brake=False,
            manual_gear_shift=False,
        )

        if self.with_gui:
            # override control by keyboard control (if any control)
            is_control_keyboard, control_keyboard = self._controller.parse_events(
                timestamp - self.prev_timestamp
            )
            if is_control_keyboard:
                control.throttle = control_keyboard.throttle
                control.brake = control_keyboard.brake
                control.hand_brake = control_keyboard.hand_brake

            self.agent_engaged = True
            self._hic.run_interface(input_data, {})

        self.prev_timestamp = timestamp

        self._vehicle_control_event.clear()

        return control

    def _translate_dm_command(self, timestamp: int) -> Tuple[int, int, int]:
        dm_command = self._dm_command.val

        dm = self._dm_controller
        dm.update_values(self._locmap, timestamp)
        dm.masterControl(timestamp, dm_command)
        dm.update_controls()

        return dm.get_commands()

    def _on_vehicle_control(self, data: int):
        if self._vehicle_control_event.is_set():
            # throw away data if previous data is not yet processed
            return

        self._dm_command.val = data
        self._vehicle_control_event.set()

    def set_egovehicle(self, ego_vehicle):
        super().set_egovehicle(ego_vehicle)
        self._gnss_handler.set_ego_vehicle(ego_vehicle)

    def get_sensor_listener(self, sensor_type: str) -> Callable[[int], None]:
        if sensor_type == "sensor.camera.rgb":
            return self._camera_handler.process_camera_sensor

        if sensor_type == "sensor.lidar.ray_cast":
            return self._lidar_handler.process_lidar_sensor

        if sensor_type == "sensor.other.gnss":
            return self._gnss_handler.process_gnss_sensor

        self._log.warn("Sensor of type %s is not supported. Will be ignored.", sensor_type)
        return self._nop

    def _nop(self, _: int):
        pass

    def destroy(self):
        super().destroy()
        try:
            self._camera_handler.destroy()
        except AttributeError:
            pass
        try:
            self._lidar_handler.destroy()
        except AttributeError:
            pass
        try:
            self._gnss_handler.destory()
        except AttributeError:
            pass
        try:
            self._control_receiver.destroy()
        except AttributeError:
            pass
