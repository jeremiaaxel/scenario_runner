import carla
import json

import pygame
# modifiers
from pygame.locals import KMOD_CTRL
# keys
from pygame.locals import K_ESCAPE # escape, quit
from pygame.locals import K_DOWN, K_s # decceleration
from pygame.locals import K_UP, K_w # acceleration
from pygame.locals import K_q   # quit
from pygame.locals import K_SPACE # hand brake
from pygame.locals import K_h   # horn

from typing import Tuple, Union

class KeyboardControl(object):

    """
    Keyboard control for the human agent
    """

    def __init__(self, configs: Union[dict, None]=None):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._horn = False
        self._steer_cache = 0.0
        self._clock = pygame.time.Clock()
        self._is_control = False

        # Get the mode
        if configs:
            self._mode = configs.get("mode", "normal")
            self._endpoint = configs.get("file", None)

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
            is_control = entry['control']['is_control']
            control = carla.VehicleControl(throttle=entry['control']['throttle'],
                                           steer=entry['control']['steer'],
                                           brake=entry['control']['brake'],
                                           hand_brake=entry['control']['hand_brake'],
                                           reverse=entry['control']['reverse'],
                                           manual_gear_shift=entry['control']['manual_gear_shift'],
                                           gear=entry['control']['gear'])
            self._control_list.append((is_control, control))

    def parse_events(self, timestamp) -> Tuple[bool, carla.VehicleControl]:
        """
        Parse the keyboard events and set the vehicle controls accordingly
        returns: true if there is any keyboard event, and the vehicle control
        """
        # Move the vehicle
        if self._mode == "playback":
            self._parse_json_control()
        else:
            keys_pressed = pygame.key.get_pressed()
            self._parse_vehicle_keys(keys_pressed, timestamp * 1000)

        # Record the control
        if self._mode == "log":
            self._record_control()

        return self._is_control, self._control

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
                    return 
                if event.key == K_q:
                    self._is_control = True
                    self._control.gear = 1 if self._control.reverse else -1
                    self._control.reverse = self._control.gear < 0

        if keys[K_UP] or keys[K_w]:
            self._control.throttle = 0.6
        else:
            self._control.throttle = 0.0

        self._horn = True if keys[K_h] else False

        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

        self._is_control = any(keys)

    def _parse_json_control(self):
        """
        Gets the control corresponding to the current frame
        """

        if self._index < len(self._control_list):
            self._is_control, self._control = self._control_list[self._index][1]
            self._index += 1
        else:
            print("JSON file has no more entries")

    def _record_control(self):
        """
        Saves the list of control into a json file
        """

        new_record = {
            'control': {
                'is_control': self._is_control,
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