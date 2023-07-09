import pygame
import math
import os

from customs.autoagents.components.FadingText import FadingText
from customs.helpers.blueprints import get_actor_display_name
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


class HumanInterface(object):

    """
    Class to control a vehicle manually for debugging purposes
    """
    _info_text = []
    _show_info = True
    ego_vehicle = None

    def __init__(self, title=None, width=640, height=403):
        self._title = title
        self._width = width
        self._height = height
        self._surface = None
        self._server_clock = pygame.time.Clock()

        pygame.font.init()
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode(
            (self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption(self._title)

        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self._notifications = FadingText(
            font, (self._width, 40), (0, self._height - 40))

    def update_info(self, imu_data, gnss_data, other_data=None):
        def get_heading(compass):
            heading = 'N' if compass > 270.5 or compass < 89.5 else ''
            heading += 'S' if 90.5 < compass < 269.5 else ''
            heading += 'E' if 0.5 < compass < 179.5 else ''
            heading += 'W' if 180.5 < compass < 359.5 else ''
            return heading

        def array_to_string(arr):
            result = f""
            for idx, item in enumerate(arr):
                result += f"{item:>5.2f}"
                if idx != len(arr) - 1:
                    result += f","
            return result

        def get_nearby_actors_info():
            def distance(transform1, transform2):
                return math.sqrt((transform1.x - transform2.location.x)**2 + (transform1.y - transform2.location.y)**2 + (transform1.z - transform2.location.z)**2)

            actors_exception = ["controller.ai.walker"]
            info_text = ["Nearby actors (camera):"]

            actors = CarlaDataProvider.get_actors()
            actors = [(id, actor) for id, actor in actors if actor is not None and actor.is_alive and
                      actor.type_id not in actors_exception and id != self.ego_vehicle.id]
            vehicles = [(distance(actor.get_location(), t_camera), actor)
                        for id, actor in actors]
            for d, vehicle in sorted(vehicles, key=lambda vehicles: vehicles[0]):
                if d > 200.0:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                info_text.append(f'{d:>9.2f} m {vehicle_type}')

            return info_text

        if other_data is None:
            other_data = dict()

        # See sensor_interface for index reference
        v = self.ego_vehicle.get_velocity()
        speed = math.sqrt(v.x**2 + v.y**2 + v.z**2)
        accelerometer = imu_data.get('accelerometer')
        gyroscope = imu_data.get('gyroscope')
        compass = imu_data.get('compass')
        lat, lon = gnss_data[0:2]

        t = None
        if self.ego_vehicle is not None:
            t = self.ego_vehicle.get_transform()

        t_camera = None
        _camera = CarlaDataProvider.get_sensor_by_id('Center')
        if _camera is not None:
            t_camera = _camera.get_transform()

        heading = get_heading(compass)

        accelerometer = [abs(x) if x == 0 else x for x in accelerometer]
        gyroscope = [abs(x) if x == 0 else x for x in gyroscope]

        self._info_text = [
            f'{"Server FPS":<10}: {self.server_fps:.2f} fps',
            '',
            f'{"Speed":<10}: {speed:.2f} m/s',
            f'{"Compass":<10}: {compass:.2f}\N{DEGREE SIGN} {heading}',
            f'{"Accelero":<10}: {array_to_string(accelerometer)}',
            f'{"Gyroscop":<10}: {array_to_string(gyroscope)}',
            f'{"GNSS":<10}: {lat:>6.2f} {lon:>6.2f}',
            '',
            f'{"Is horn:":<10} {other_data.get("is_horn", False)}',
            '']

        if t_camera:
            self._info_text.extend([
                "(camera)",
                f"{'Location':<9}: ({t_camera.location.x:>6.2f}, {t_camera.location.y:>6.2f})"
            ])

        if t:
            self._info_text.extend(
                [
                    f"{'Location':<9}: ({t.location.x:>6.2f}, {t.location.y:>6.2f})",
                    f"{'Height':<9}: {t.location.z:>6.2f}"
                ]
            )

        self._info_text.extend(
            [
                "",
                *get_nearby_actors_info()
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
                    points = [(x + 8, v_offset + 8 + (1.0 - y) * 30)
                              for x, y in enumerate(item)]
                    pygame.draw.lines(
                        self._display, (255, 136, 0), False, points, 2)
                item = None
                v_offset += 18
            elif isinstance(item, tuple):
                if isinstance(item[1], bool):
                    rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                    pygame.draw.rect(
                        self._display, (255, 255, 255), rect, 0 if item[1] else 1)
                else:
                    rect_border = pygame.Rect(
                        (bar_h_offset, v_offset + 8), (bar_width, 6))
                    pygame.draw.rect(
                        self._display, (255, 255, 255), rect_border, 1)
                    f = (item[1] - item[2]) / (item[3] - item[2])
                    if item[2] < 0.0:
                        rect = pygame.Rect(
                            (bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                    else:
                        rect = pygame.Rect(
                            (bar_h_offset, v_offset + 8), (f * bar_width, 6))
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

    def run_interface(self, input_data, other_data=None):
        """
        Run the GUI
        """
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()

        # process sensor data
        image_center = input_data['Center'][1][:, :, -2::-1]
        imu_data = HumanInterface.parse_imu_data(input_data['IMU'][1])
        gnss_data = input_data['GNSS'][1]

        # display image
        self._surface = pygame.surfarray.make_surface(
            image_center.swapaxes(0, 1))
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        self.update_info(imu_data, gnss_data, other_data)
        self.render_info()
        pygame.display.flip()

    def quit_interface(self):
        """
        Stops the pygame window
        """
        pygame.quit()

    def set_egovehicle(self, egovehicle):
        self.ego_vehicle = egovehicle
