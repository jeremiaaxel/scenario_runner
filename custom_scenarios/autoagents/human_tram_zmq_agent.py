#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides a human agent to control the acceleration/decceleration of ego vehicle via keyboard.
Steering is done automatically by the vehicle to follow the route that's been set.
"""

from __future__ import print_function
from dataclasses import dataclass
from typing import Tuple
from multisensors.displays.FadingText import FadingText

from multisensors.displays.KeyboardControl import KeyboardControl

try:
    import pygame
    # modifiers
    from pygame.locals import KMOD_CTRL
    # keys
    from pygame.locals import K_ESCAPE # escape, quit
    from pygame.locals import K_DOWN, K_s # decceleration
    from pygame.locals import K_UP, K_w # acceleration
    from pygame.locals import K_q   # quit
    from pygame.locals import K_SPACE # hand brake
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import carla
import json
import os
import math
import zmq
import logging

from srunner.autoagents.autonomous_agent import AutonomousAgent
from srunner.autoagents.npc_agent import NpcAgent
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

class HumanInterface(object):

    """
    Class to control a vehicle manually for debugging purposes
    """
    _info_text = []
    _show_info = True
    ego_vehicle = None

    def __init__(self):
        self._width = 800
        self._height = 600
        self._surface = None

        pygame.init()
        pygame.font.init()
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode((self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Human Tram ZMQ Agent")
        
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self._notifications = FadingText(font, (self._width, 40), (0, self._height - 40))

    def update_info(self, imu_data, gnss_data): 
        def get_heading(compass):
            heading = 'N' if compass > 270.5 or compass < 89.5 else ''
            heading += 'S' if 90.5 < compass < 269.5 else ''
            heading += 'E' if 0.5 < compass < 179.5 else ''
            heading += 'W' if 180.5 < compass < 359.5 else ''
            return heading

        def array_to_string(arr):
            result = f""
            for idx, item in enumerate(arr):
                result += f"{item:2f}"
                if idx != len(arr) - 1:
                    result += f","
            return result

        # See sensor_interface for index reference
        accelerometer = imu_data.get('accelerometer')
        gyroscope = imu_data.get('gyroscope')
        compass = imu_data.get('compass')
        lat, lon = gnss_data[0:2]

        t = None
        if self.ego_vehicle is not None:
            t = self.ego_vehicle.get_transform()

        heading = get_heading(compass)
        self._info_text = [
            # 'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)),
            f'Compass: {compass:2f}\N{DEGREE SIGN} {heading}',
            f'Accelero: {array_to_string(accelerometer)}',
            f'Gyroscop: {array_to_string(gyroscope)}',
            f'GNSS: {lat:2f} {lon:2f}',
            '']
        
        if t:
            self._info_text.extend(
                [
                    'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
                    'Height:  % 18.0f m' % t.location.z,
                ]
            )
    
    def render_info(self):
        info_surface = pygame.Surface((220, self._height))
        info_surface.set_alpha(100)
        self._display.blit(info_surface, (0, 0))
        v_offset = 4
        bar_h_offset = 100
        bar_width = 106
        for item in self._info_text:
            if v_offset + 18 > self._height:
                break
            if isinstance(item, list):
                if len(item) > 1:
                    points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                    pygame.draw.lines(self._display, (255, 136, 0), False, points, 2)
                item = None
                v_offset += 18
            elif isinstance(item, tuple):
                if isinstance(item[1], bool):
                    rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                    pygame.draw.rect(self._display, (255, 255, 255), rect, 0 if item[1] else 1)
                else:
                    rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                    pygame.draw.rect(self._display, (255, 255, 255), rect_border, 1)
                    f = (item[1] - item[2]) / (item[3] - item[2])
                    if item[2] < 0.0:
                        rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                    else:
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                    pygame.draw.rect(self._display, (255, 255, 255), rect)
                item = item[0]
            if item:  # At this point has to be a str.
                surface = self._font_mono.render(item, True, (255, 255, 255))
                self._display.blit(surface, (8, v_offset))
            v_offset += 18

    @staticmethod
    def parse_imu_data(imu_data):
        limits = (-99.9, 99.9)
        def parse_accelerometer(accelerometer):
            return (max(limits[0], min(limits[1], accelerometer[0])),
                max(limits[0], min(limits[1], accelerometer[1])),
                max(limits[0], min(limits[1], accelerometer[2])))
        def parse_gyroscope(gyroscope):
            return (max(limits[0], min(limits[1], gyroscope[0])),
                max(limits[0], min(limits[1], gyroscope[1])),
                max(limits[0], min(limits[1], gyroscope[2])))
        def parse_compass(compass):
            return (math.degrees(compass) - 90) % 360

        accelerometer = imu_data[0:3]
        gyroscope = imu_data[3:6]
        compass = imu_data[6]
        return {'accelerometer': parse_accelerometer(accelerometer), 
            'gyroscope': parse_gyroscope(gyroscope), 
            'compass': parse_compass(compass)}

    def run_interface(self, input_data):
        """
        Run the GUI
        """
        # process sensor data
        image_center = input_data['Center'][1][:, :, -2::-1]
        imu_data = HumanInterface.parse_imu_data(input_data['IMU'][1])
        gnss_data = input_data['GNSS'][1]

        # display image
        self._surface = pygame.surfarray.make_surface(image_center.swapaxes(0, 1))
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        self.update_info(imu_data, gnss_data)
        self.render_info()
        pygame.display.flip()

    def quit_interface(self):
        """
        Stops the pygame window
        """
        pygame.quit()

    def set_egovehicle(self, egovehicle):
        self.ego_vehicle = egovehicle

# TODO: move to another location
ADDR = "127.0.0.1"
PUB_PORT = "8080"
SUB_PORT = "8000"

CAMERA_TOPIC = b"" # TODO: standardize
CONTROL_TOPIC = b"carla/ego_vehicle/control"

class ZmqControl(object):
    """
    Sends: all sensors data
    Receives: acceleration and brake
    """
    
    def __init__(self, pub_addr: str = f"{ADDR}:{PUB_PORT}", sub_addr: str = f"{ADDR}:{SUB_PORT}") -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ZMQ control")

        self.pub_addr = pub_addr
        self.sub_addr = sub_addr

        context = zmq.Context()
        pub_socket = context.socket(zmq.PUB)
        pub_socket.bind(self.pub_addr)

        sub_socket = context.socket(zmq.SUB)
        sub_socket.bind(self.sub_addr)

        self.pub_socket = pub_socket
        self.sub_socket = sub_socket

    def send_sensors(self, sensors_data) -> bool:
        ""
        # TODO: send sensor via ZMQ
        pass

    def receive_control_raw(self) -> str:
        """
        Receive control as string 
        """
        # TODO: receive sensor via ZMQ
        topic, msg = self.sub_socket.recv_multipart()
        if topic != CONTROL_TOPIC:
            return

        topic, msg = topic.decode('utf-8'), msg.decode('utf-8')
        self.logger.info(f"Received:\n\ttopic: {topic}\n\tmessage: {msg}")
        return msg

    def receive_control(self) -> carla.VehicleControl:
        msg = self.receive_control_raw()
        return ZmqControl.to_vehicle_control(msg)

    @staticmethod
    def to_vehicle_control(string: str) -> carla.VehicleControl:
        vehicle_control = carla.VehicleControl()
        # TODO: standardize string format
        return vehicle_control


class HumanTramZmqAgent(NpcAgent):

    """
    Human tram agent to control the ego vehicle via zmq
    """

    current_control = None
    agent_engaged = False
    prev_timestamp = 0
    width = 800
    height = 600
    ego_vehicle = None

    def setup(self, path_to_conf_file=None):
        """
        Setup the agent parameters
        """

        super().setup(path_to_conf_file)
        self._hic = HumanInterface()
        self._controller = KeyboardControl(path_to_conf_file)
        self._zmqcontroller = ZmqControl()

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
             'width': 800, 'height': 600, 'fov': 100},
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
        Steering: NPC agent
        Acceleration: From ZMQ
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
        """
        Overriden controls by keyboards:
          - throttle
          - brake
          - hand_brake
        """
        is_control_keyboard, control_keyboard = self._controller.parse_events(timestamp - self.prev_timestamp)
        if is_control_keyboard:
            control.throttle = control_keyboard.throttle
            control.brake = control_keyboard.brake
            control.hand_brake = control_keyboard.hand_brake
        
        self.agent_engaged = True
        self._hic.run_interface(input_data)

        self.prev_timestamp = timestamp
        return control

    def set_egovehicle(self, egovehicle):
        self.ego_vehicle = egovehicle
        self._hic.set_egovehicle(egovehicle)

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

        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

        if len(keys) > 0:
            self._is_control = True

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
