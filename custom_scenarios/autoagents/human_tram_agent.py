#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function

from multisensors.displays.HUD import HUD
from multisensors.displays.KeyboardControl import KeyboardControl
from multisensors.displays.WorldSR import WorldSR
from multisensors.utils.get_sensors_json import get_sensors_json

try:
    import pygame
    # modifiers
    from pygame.locals import KMOD_CTRL
    # keys
    from pygame.locals import K_ESCAPE # escape, quit
    from pygame.locals import K_DOWN, K_s # decceleration
    from pygame.locals import K_UP, K_w # acceleration
    from pygame.locals import K_LEFT, K_a # left
    from pygame.locals import K_RIGHT, K_d # right
    from pygame.locals import K_q   # quit
    from pygame.locals import K_SPACE # hand brake
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import carla
import json

from srunner.autoagents.autonomous_agent import AutonomousAgent
from srunner.autoagents.npc_agent import NpcAgent

class HumanInterface(object):

    """
    Class to control a vehicle manually for debugging purposes
    """

    def __init__(self):
        self._width = 800
        self._height = 600
        self._surface = None

        pygame.init()
        pygame.font.init()
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Tram Agent")

    def run_interface(self, input_data):
        """
        Run the GUI
        """
        # process sensor data
        image_center = input_data['Center'][1][:, :, -2::-1]

        # display image
        self._surface = pygame.surfarray.make_surface(image_center.swapaxes(0, 1))
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        pygame.display.flip()

    def quit_interface(self):
        """
        Stops the pygame window
        """
        pygame.quit()

class HumanTramAgent(NpcAgent):

    """
    Human tram agent to control the ego vehicle via keyboard
    """

    current_control = None
    agent_engaged = False
    prev_timestamp = 0
    width = 800
    height = 600
    client = carla.Client('localhost', 2000)
    client.set_timeout(20.0)

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)
        self.agent_engaged = False
        self.prev_timestamp = 0
        self._hic = HumanInterface()
        self._controller = KeyboardControl(path_to_conf_file)

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
            {'id': 'Center', 'type': 'sensor.camera.rgb', 'x': 4.5, 'y': 0.0, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                    'width': 800, 'height': 600, 'fov': 100},
            {'id': 'GNSS', 'type': 'sensor.other.gnss', 'x': 0.7, 'y': -0.4, 'z': 1.60, 'id': 'GNSS'}
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = super().run_step(input_data, timestamp)
        steering = control.steer
        del control
        
        self.agent_engaged = True
        self._hic.run_interface(input_data)

        control = self._controller.parse_events(timestamp - self.prev_timestamp)
        # take control of steering
        control.steer = steering
        self.prev_timestamp = timestamp

        return control

    def destroy(self):
        """
        Cleanup
        """
        self._hic.quit_interface = True


class KeyboardControl(object):

    """
    Keyboard control for the human agent
    """

    def __init__(self, path_to_conf_file=None):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0
        self._clock = pygame.time.Clock()

        # Get the mode
        if path_to_conf_file:

            with (open(path_to_conf_file, "r")) as f:
                lines = f.read().split("\n")
                self._mode = lines[0].split(" ")[1]
                self._endpoint = lines[1].split(" ")[1]

            # Get the needed vars
            if self._mode == "log":
                self._log_data = {'records': []}

            elif self._mode == "playback":
                self._index = 0
                self._control_list = []

                with open(self._endpoint) as fd:
                    try:
                        self._records = json.load(fd)
                        self._json_to_control()
                    except ValueError:
                        # Moving to Python 3.5+ this can be replaced with json.JSONDecodeError
                        pass
        else:
            self._mode = "normal"
            self._endpoint = None

    def _json_to_control(self):
        """
        Parses the json file into a list of carla.VehicleControl
        """

        # transform strs into VehicleControl commands
        for entry in self._records['records']:
            control = carla.VehicleControl(throttle=entry['control']['throttle'],
                                           steer=entry['control']['steer'],
                                           brake=entry['control']['brake'],
                                           hand_brake=entry['control']['hand_brake'],
                                           reverse=entry['control']['reverse'],
                                           manual_gear_shift=entry['control']['manual_gear_shift'],
                                           gear=entry['control']['gear'])
            self._control_list.append(control)

    def parse_events(self, timestamp):
        """
        Parse the keyboard events and set the vehicle controls accordingly
        """
        # Move the vehicle
        if self._mode == "playback":
            self._parse_json_control()
        else:
            self._parse_vehicle_keys(pygame.key.get_pressed(), timestamp * 1000)

        # Record the control
        if self._mode == "log":
            self._record_control()

        return self._control

    def _parse_vehicle_keys(self, keys, milliseconds):
        """
        Calculate new vehicle controls based on input keys
        """
        def _is_quit_shortcut(key):
            return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYUP:
                if _is_quit_shortcut(event.key):
                    return True
                if event.key == K_q:
                    self._control.gear = 1 if self._control.reverse else -1
                    self._control.reverse = self._control.gear < 0

        if keys[K_UP] or keys[K_w]:
            self._control.throttle = 0.6
        else:
            self._control.throttle = 0.0

        self._steer_cache = 0.0
        # steer_increment = 3e-4 * milliseconds
        # if self._mode == "normal":
        #     if keys[K_LEFT] or keys[K_a]:
        #         self._steer_cache -= steer_increment
        #     elif keys[K_RIGHT] or keys[K_d]:
        #         self._steer_cache += steer_increment
        #     else:
        #         self._steer_cache = 0.0

        # self._steer_cache = min(0.95, max(-0.95, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_json_control(self):
        """
        Gets the control corresponding to the current frame
        """

        if self._index < len(self._control_list):
            self._control = self._control_list[self._index]
            self._index += 1
        else:
            print("JSON file has no more entries")

    def _record_control(self):
        """
        Saves the list of control into a json file
        """

        new_record = {
            'control': {
                'throttle': self._control.throttle,
                'steer': self._control.steer,
                'brake': self._control.brake,
                'hand_brake': self._control.hand_brake,
                'reverse': self._control.reverse,
                'manual_gear_shift': self._control.manual_gear_shift,
                'gear': self._control.gear
            }
        }

        self._log_data['records'].append(new_record)

    def __del__(self):
        """
        Delete method
        """
        # Get ready to log user commands
        if self._mode == "log" and self._log_data:
            with open(self._endpoint, 'w') as fd:
                json.dump(self._log_data, fd, indent=4, sort_keys=True)
