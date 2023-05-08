#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

import pygame
import py_trees

from customs.autoagents.components.HumanInterface import HumanInterface
from customs.autoagents.components.KeyboardControl import KeyboardControl
from customs.autoagents.tram_agent import TramAgent
from customs.helpers.json_to_dict import json_to_dict

class HumanTramAgent(TramAgent):
    """
    Human tram agent to control the ego vehicle via keyboard
    """

    agent_engaged = False
    with_gui = True
    prev_timestamp = 0

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)
        configs = json_to_dict(path_to_conf_file)
        self.with_gui = configs.get("with_gui", self.with_gui)
        keyboard_config = configs.get("keyboard", None)

        pygame.init()
        if self.with_gui:
            self._hic = HumanInterface(title=self.__class__.__name__)
        self._controller = KeyboardControl(keyboard_config)

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        # Change steering: Steering from NPC Agent
        control_super = super().run_step(input_data, timestamp)
        self.is_keyboard_control, control = self._controller.parse_events(timestamp - self.prev_timestamp)
        is_horn = self._controller._horn
        other_data = {
            'is_horn': is_horn
        }
        py_trees.blackboard.Blackboard().set("is_ego_vehicle_horn", is_horn, overwrite=True)
        control.steer = control_super.steer
        
        self.agent_engaged = True
        if self.with_gui:
            self._hic.run_interface(input_data, other_data)
        self.prev_timestamp = timestamp

        return control

    def set_egovehicle(self, egovehicle):
        super().set_egovehicle(egovehicle)
        if self.with_gui:
            self._hic.set_egovehicle(egovehicle)

    def destroy(self):
        """
        Cleanup
        """
        if self.with_gui:
            self._hic.quit_interface = True
