#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

from customs.autoagents.human_tram_agent import HumanTramAgent

# has to append PYTHONPATH with $HOME/Documents/khansa/rilis3
from decision_maker import DecisionMaker

class SilsAgent(HumanTramAgent):
    """
    Human tram agent to control the ego vehicle via ZMQ
    """

    agent_engaged = False
    prev_timestamp = 0
    ego_vehicle = None
    is_setup = False

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)

    def post_setup(self):
        world = CarlaDataProvider.get_world()
        wmap = CarlaDataProvider.get_map()
        route = CarlaDataProvider.get_ego_vehicle_route()

        start_point = route[0][0] # tuple(location, road type)
        destination = route[-1][0]

        # TODO: copy the contents of $HOME/Documents/khansa/rilis3/main.py's setup (before the main loop) to here
        self.decision_maker = DecisionMaker(world, 
                                            wmap, 
                                            self.ego_vehicle, 
                                            start_loc=start_point,
                                            dest_loc=destination,
                                            debug=False)

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
    
        # get ego vehicle and route
        if not self.is_setup:
            self.post_setup()
            self.is_setup = True

        control_super = super().run_step(input_data, timestamp)
        control = self.decision_maker.run_step(timestamp)

        # print(f"Controller2d | Throttle: {control.throttle} | Brake: {control.brake}")

        # Output controller command to CARLA server
        control.steer = control_super.steer

        # override control by keyboard control (if any control)
        if self.is_keyboard_control:
            control.throttle = control_super.throttle
            control.brake = control_super.brake
            control.hand_brake = control_super.hand_brake
        # print(f"Result | Throttle: {control.throttle} | Brake: {control.brake}")

        return control
