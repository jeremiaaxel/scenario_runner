#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

from customs.autoagents.zmq_agent.ZmqControl import ZmqControl
from customs.autoagents.components.HumanInterface import HumanInterface
from customs.autoagents.components.KeyboardControl import KeyboardControl
from customs.autoagents.human_tram_agent import HumanTramAgent

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

    # sensors are set by TramAgent
    def sensors(self):
        return super().sensors()
    
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
        # TODO: publish sensors data via ZMQ
        self._zmqcontroller.send_sensors(input_data)

        # acceleration: from ZMQ
        # TODO: subscribe acceleration data via ZMQ
        control = self._zmqcontroller.receive_control()

        # steering: from NPC agent
        control_super = super().run_step(input_data, timestamp)
        control.steer = control_super.steer

        # override control by keyboard control (if any control)
        is_control_keyboard, control_keyboard = self._controller.parse_events(timestamp - self.prev_timestamp)
        if is_control_keyboard:
            control.throttle = control_keyboard.throttle
            control.brake = control_keyboard.brake
            control.hand_brake = control_keyboard.hand_brake
        
        self.agent_engaged = True
        self._hic.run_interface(input_data)

        self.prev_timestamp = timestamp
        return control
