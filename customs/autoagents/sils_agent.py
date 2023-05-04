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

from customs.autoagents.zmq_agent.ZmqControl import ZmqControl
from customs.autoagents.components.HumanInterface import HumanInterface
from customs.autoagents.components.KeyboardControl import KeyboardControl
from customs.autoagents.human_tram_agent import HumanTramAgent

# has to append PYTHONPATH with $HOME/Documents/khansa/rilis3
from controller2d import Controller2D 
from perception_system import Perception
from lokalisasi import LocMap as Localisasi
from grs_dm_class import grs_tram_state, HLC_state, state_transition, dm_tram_state
from grs_dm import getCommand, updateDmCommand

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
        _dt = 1.0 / 20.0
        _args_lateral_dict = {'K_P': 1.02, 'K_I': 0.001, 'K_D': 0.2, 'dt': _dt}
        _args_longitudinal_dict = {'K_P': 5, 'K_I': 0.3, 'K_D': 0.13, 'dt': _dt}   

        world = CarlaDataProvider.get_world()
        map = CarlaDataProvider.get_map()
        route = CarlaDataProvider.get_ego_vehicle_route()

        start_point = route[0][0] # tuple(location, road type)
        destination = route[-1][0]

        self.StateTransition = state_transition()
        self.HLC = HLC_state()
        self.tram = grs_tram_state()
        self.DmTramState = dm_tram_state()
        self.Dm_RailObstacleStates = []


        self.perception = Perception(world)
        self.localisasi = Localisasi(map, self.ego_vehicle)
        self.localisasi.set_destination(start_point, destination)
        self._controller2d = Controller2D(self.ego_vehicle, map, self.localisasi.wpt, self.localisasi.lateral_route, _args_lateral_dict, _args_longitudinal_dict)

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

        updateDmCommand(self.StateTransition, self.HLC, self.DmTramState.t, self.Dm_RailObstacleStates,
                        self.tram.SpeedLimit, self.DmTramState.v,
                        self.StateTransition.SafeEmergencyDistance + 15)
        self.tram.ManualPower = getCommand(self.HLC)
        self._controller2d.update_values(self.localisasi, timestamp - self.prev_timestamp)
        self._controller2d.masterControl(timestamp - self.prev_timestamp, self.tram.ManualPower)
        self._controller2d.update_controls()
        throttle, _, brake = self._controller2d.get_commands()
        print(f"Controller2d | Throttle: {throttle} | Brake: {brake}")

        # Output controller command to CARLA server
        control = carla.VehicleControl()
        control.steer = control_super.steer
        control.throttle = throttle
        control.brake = brake 
        control.hand_brake = False
        control.manual_gear_shift = False

        # override control by keyboard control (if any control)
        print(f"Is keyboard: {self.is_keyboard_control}")
        if self.is_keyboard_control:
            control.throttle = control_super.throttle
            control.brake = control_super.brake
            control.hand_brake = control_super.hand_brake
        print(f"Result | Throttle: {control.throttle} | Brake: {control.brake}")

        return control
