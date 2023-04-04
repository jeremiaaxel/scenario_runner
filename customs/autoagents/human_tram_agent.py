#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

from customs.autoagents.components.HumanInterface import HumanInterface
from customs.autoagents.components.KeyboardControl import KeyboardControl
from customs.autoagents.tram_agent import TramAgent

class HumanTramAgent(TramAgent):
    """
    Human tram agent to control the ego vehicle via keyboard
    """

    agent_engaged = False
    prev_timestamp = 0

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)
        self._hic = HumanInterface()
        self._controller = KeyboardControl(path_to_conf_file)

    # sensors are set by TramAgent
    def sensors(self):
        return super().sensors()

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        # Change steering: Steering from NPC Agent
        control_super = super().run_step(input_data, timestamp)
        _, control = self._controller.parse_events(timestamp - self.prev_timestamp)
        control.steer = control_super.steer
        
        self.agent_engaged = True
        self._hic.run_interface(input_data)
        self.prev_timestamp = timestamp

        return control

    def set_egovehicle(self, egovehicle):
        super().set_egovehicle(egovehicle)
        self._hic.set_egovehicle(egovehicle)

    def destroy(self):
        """
        Cleanup
        """
        self._hic.quit_interface = True
