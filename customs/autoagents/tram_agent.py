#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

from srunner.autoagents.npc_agent import NpcAgent
import carla

class TramAgent(NpcAgent):

    """
    Tram agent to control the ego vehicle steering via NPC
    """

    agent_engaged = False
    prev_timestamp = 0
    ego_vehicle = None

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors in the following format:

        [
            ['sensor.camera.rgb', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                   'yaw': yaw, 'pitch': pitch, 'roll': roll,
                                   'width': width, 'height': height, 'fov': fov}, 'Sensor01'],
            ['sensor.camera.rgb', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                   'yaw': yaw, 'pitch': pitch, 'roll': roll,
                                   'width': width, 'height': height, 'fov': fov}, 'Sensor02'],

            ['sensor.lidar.ray_cast', {'x':x_rel, 'y': y_rel, 'z': z_rel,
                                       'yaw': yaw, 'pitch': pitch, 'roll': roll}, 'Sensor03']
        ]

        """
        sensors = [
            {'id': 'Center', 'type': 'sensor.camera.rgb', 
             'x': 5.5, 'y': 0.0, 'z': 2.3, 
             'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
             'width': 640, 'height': 403, 'fov': 110},
            {'id': 'GNSS', 'type': 'sensor.other.gnss', 
             'x': 0.7, 'y': -0.4, 'z': 1.60,
             'roll': 0.0, 'pitch': 0.0, 'yaw': 90.0},
            {'id': 'IMU', 'type': 'sensor.other.imu', 
             'x': 0.7, 'y': -0.4, 'z': 1.60,
             'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        # Change steering: Steering from NPC Agent
        control = carla.VehicleControl()
        control_super = super().run_step(input_data, timestamp)
        control.steer = control_super.steer
        
        self.agent_engaged = True
        self.prev_timestamp = timestamp

        return control

    def set_egovehicle(self, egovehicle):
        """
        Sets the ego vehicle property of an agent.
        CARLA Scenario Runner route mode doesn't insert the ego vehicle to the agent.
        """
        self.ego_vehicle = egovehicle
