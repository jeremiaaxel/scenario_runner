#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle
via keyboard. Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function
from typing import Callable
import zmq
import os
from hils_connector.carla_handlers.outbound import (
    GnssHandler,
    LidarHandler,
    CameraHandler,
)
from hils_connector.carla_handlers.inbound import ControlHandler
from threading import Event
from carla import VehicleControl

from customs.autoagents.zmq_agent.ZmqControl import ZmqControl
from customs.autoagents.components.HumanInterface import HumanInterface
from customs.autoagents.components.KeyboardControl import KeyboardControl
from customs.autoagents.human_tram_agent import HumanTramAgent


class Integer:
    def __init__(self, value: int):
        self.val = value


class HumanTramZmqAgent(HumanTramAgent):
    """
    Human tram agent to control the ego vehicle via ZMQ
    """

    agent_engaged = False
    prev_timestamp = 0
    ego_vehicle = None

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)
        self._zmqcontroller = ZmqControl()

        self._vehicle_control_event = Event()

        self._dm_command = Integer(0)

        self._setup_sensors()


    def _setup_sensors(self):
        """
        setup helper
        """
        zmq_context = zmq.Context()
        zmq_host = os.getenv("ZMQ_HOST", "167.205.66.15")

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
                raise TypeError("Invalid sensor type: {}".format(sensor["type"]))

        port = os.getenv("ZMQ_CONTROL_PORT", 5556)
        self._control_receiver = ControlHandler(
            zmq_host, port, self._on_vehicle_control, zmq_context
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
        self._vehicle_control_event.wait()

        # steering: from NPC agent
        control_super = super().run_step(input_data, timestamp)

        control = VehicleControl(
            throttle=self._dm_command.val,
            steer=control_super.steer,
            brake=self._dm_command.val,
            hand_brake=False,
            manual_gear_shift=False,
        )

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

    def _on_vehicle_control(self, data: int):
        if self._vehicle_control_event.is_set():
            # throw away data if previous data is not yet processed
            return

        self._dm_command.val = data

    def set_egovehicle(self, ego_vehicle):
        super().set_egovehicle(ego_vehicle)
        self._gnss_handler.set_ego_vehicle(ego_vehicle)

    def get_sensor_listener(self, sensor_type) -> Callable:
        if sensor_type.startswith("sensor.camera"):
            return self._camera_handler.process_camera_sensor

        if sensor_type.startswith("sensor.lidar"):
            return self._lidar_handler.process_lidar_sensor

        # gnss
        return self._gnss_handler.process_gnss_sensor

    def destroy(self):
        super().destroy()
        self._camera_handler.destroy()
        self._lidar_handler.destroy()
        self._gnss_handler.destory()
        self._control_receiver.destroy()
