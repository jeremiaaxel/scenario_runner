import pygame
import math
import os

from customs.autoagents.components.FadingText import FadingText

class HumanInterface(object):

    """
    Class to control a vehicle manually for debugging purposes
    """
    _info_text = []
    _show_info = True
    ego_vehicle = None

    def __init__(self, title=None, width=800, height=600):
        self._title = title
        self._width = width
        self._height = height
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
        pygame.display.set_caption(self._title)
        
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self._notifications = FadingText(font, (self._width, 40), (0, self._height - 40))

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
                result += f"{item:2f}"
                if idx != len(arr) - 1:
                    result += f","
            return result

        if other_data is None:
            other_data = dict()
            
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
            '',
            f'Is horn: {other_data.get("is_horn", False)}',
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

    def run_interface(self, input_data, other_data=None):
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
