# ==============================================================================
# -- SensorManager ---------------------------------------------------------------------
# ==============================================================================


# TODO: Make SensorManager as a "Manager" not as individual Sensor

import carla
import pygame
import numpy as np
from sensors.GnssSensor import GnssSensor
from sensors.RadarSensor import RadarSensor

from utils.CustomTimer import CustomTimer

from typing import Union, Tuple

class SensorManager:
    def __init__(self, world, hud, sensor_type, name, transform_dict, attached, sensor_options, display_pos):
        self.surface = None
        self.world = world
        self.hud = hud
        self.type = sensor_type
        self.name = name if name is not None else sensor_type
        self.transform_dict = transform_dict
        self.attached = attached
        self.sensor_options = sensor_options
        self.display_pos = display_pos
        print(f"Spawning {sensor_type}: {name}...", end="")
        self.sensor = self.init_sensor(sensor_type, transform_dict, attached, sensor_options)
        if self.sensor is not None:
            print(f"done")
        else:
            print(f"fail")
            print(f"Sensor {sensor_type} is not known.")

        self.timer = CustomTimer()

        self.time_processing = 0.0
        self.tics_processing = 0

        self.hud.add_sensor(self)

    @staticmethod
    def get_transform_from_dict(transform: dict, boundings: Tuple[float,float,float], defaults: Tuple[Tuple[float,float,float], Tuple[float,float,float]]) -> carla.Transform:
        def get_location(axis: Union[dict,None], default_val: Union[int,float], relative_pos: Union[int,float]) -> Union[int,float]:
            """
            Translates axis as dict into its value.\\
            from: axis: {
                'relative': True
                'value': 4
            }
            into: relative + 4\\
            returns default value if None
            """
            if axis is None:
                return default_val
            axis_val = relative_pos if axis.get('relative', False) else 0 # if relative, relative_pos + value, else 0 + value
            axis_val += axis.get('value', default_val)
            return axis_val

        bound_x, bound_y, bound_z = boundings
        default_axes, default_rots = defaults
        default_x, default_y, default_z = default_axes
        default_pitch, default_yaw, default_roll = default_rots

        x = get_location(transform.get('x'), default_val=default_x, relative_pos=bound_x)
        y = get_location(transform.get('y'), default_val=default_y, relative_pos=bound_y)
        z = get_location(transform.get('z'), default_val=default_z, relative_pos=bound_z)

        location = carla.Location(x=x, y=y, z=z)
        rotation = carla.Rotation(
                    pitch=transform.get('pitch', default_pitch),
                    yaw=transform.get('yaw', default_yaw),
                    roll=transform.get('roll', default_roll))
        return carla.Transform(location, rotation)

    def init_sensor(self, sensor_type, transform_dict, attached, sensor_options):
        bound_x = attached.bounding_box.extent.x
        bound_y = attached.bounding_box.extent.y
        bound_z = attached.bounding_box.extent.z

        default_x, default_y, default_z = 0, 0, 0
        default_pitch, default_yaw, default_roll = 0, 0, 0

        if transform_dict is not None:
            transform = SensorManager.get_transform_from_dict(transform_dict,
                (bound_x, bound_y, bound_z),
                ((default_x, default_y, default_z),
                (default_pitch, default_yaw, default_roll)))
        else:
            transform = carla.Transform(carla.Location(x=default_x, y=default_y, z=default_z),
                                        carla.Rotation(pitch=default_pitch, yaw=default_yaw, roll=default_roll))

        if sensor_type == 'RGBCamera':
            camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
            hud_size = self.hud.get_display_size()
            camera_bp.set_attribute('image_size_x', str(hud_size[0]))
            camera_bp.set_attribute('image_size_y', str(hud_size[1]))

            for key in sensor_options:
                camera_bp.set_attribute(key, sensor_options[key])

            camera = self.world.spawn_actor(camera_bp, transform, attach_to=attached)
            camera.listen(self.save_rgb_image)

            return camera

        elif sensor_type == 'LiDAR':
            lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.ray_cast')
            lidar_bp.set_attribute('range', '100')
            lidar_bp.set_attribute('dropoff_general_rate',
                                   lidar_bp.get_attribute('dropoff_general_rate').recommended_values[0])
            lidar_bp.set_attribute('dropoff_intensity_limit',
                                   lidar_bp.get_attribute('dropoff_intensity_limit').recommended_values[0])
            lidar_bp.set_attribute('dropoff_zero_intensity',
                                   lidar_bp.get_attribute('dropoff_zero_intensity').recommended_values[0])

            for key in sensor_options:
                lidar_bp.set_attribute(key, sensor_options[key])

            lidar = self.world.spawn_actor(lidar_bp, transform, attach_to=attached)

            lidar.listen(self.save_lidar_image)

            return lidar

        elif sensor_type == 'SemanticLiDAR':
            lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.ray_cast_semantic')
            lidar_bp.set_attribute('range', '100')

            for key in sensor_options:
                lidar_bp.set_attribute(key, sensor_options[key])

            lidar = self.world.spawn_actor(lidar_bp, transform, attach_to=attached)

            lidar.listen(self.save_semanticlidar_image)

            return lidar

        elif sensor_type == "Radar":
            return RadarSensor(attached, transform)

        elif sensor_type == "GNSS":
            return GnssSensor(attached, transform)

        else:
            print(f"Sensor type: {sensor_type} is not known.")
            return None

    def flip(self):
        self.sensor.stop()
        self.sensor.destroy()
        self.transform_dict['yaw'] = self.transform_dict.get('yaw', 00) + 180
        self.sensor = self.init_sensor(self.type, self.transform_dict, self.attached, self.sensor_options)

    def get_sensor(self):
        return self.sensor

    def save_rgb_image(self, image):
        t_start = self.timer.time()

        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]

        if self.hud.render_enabled():
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        t_end = self.timer.time()
        self.time_processing += (t_end - t_start)
        self.tics_processing += 1

    def save_lidar_image(self, image):
        t_start = self.timer.time()

        disp_size = self.hud.get_display_size()
        lidar_range = 2.0 * float(self.sensor_options['range'])

        points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0] / 4), 4))
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(disp_size) / lidar_range
        lidar_data += (0.5 * disp_size[0], 0.5 * disp_size[1])
        lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (disp_size[0], disp_size[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)

        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)

        if self.hud.render_enabled():
            self.surface = pygame.surfarray.make_surface(lidar_img)

        t_end = self.timer.time()
        self.time_processing += (t_end - t_start)
        self.tics_processing += 1

    def save_semanticlidar_image(self, image):
        t_start = self.timer.time()

        disp_size = self.hud.get_display_size()
        lidar_range = 2.0 * float(self.sensor_options['range'])

        points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0] / 6), 6))
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(disp_size) / lidar_range
        lidar_data += (0.5 * disp_size[0], 0.5 * disp_size[1])
        lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (disp_size[0], disp_size[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)

        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)

        if self.hud.render_enabled():
            self.surface = pygame.surfarray.make_surface(lidar_img)

        t_end = self.timer.time()
        self.time_processing += (t_end - t_start)
        self.tics_processing += 1

    # def save_radar_image(self, radar_data):
    #     t_start = self.timer.time()
    #     points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
    #     points = np.reshape(points, (len(radar_data), 4))

    #     t_end = self.timer.time()
    #     self.time_processing += (t_end - t_start)
    #     self.tics_processing += 1

    def render(self):
        if self.surface is not None:
            offset = self.hud.get_display_offset(self.display_pos)
            self.hud.display.blit(self.surface, offset)

    def stop(self):
        print(f"Stopping sensor {self.name}...", end="")
        if self.sensor is None:
            print("already destroyed")
            return
        self.sensor.stop()
        print("done")

    def destroy(self):
        print(f"Destroying sensor {self.name}...", end="")
        if self.sensor is None:
            print("already destroyed")
            return
        self.sensor.destroy()
        print("done")
