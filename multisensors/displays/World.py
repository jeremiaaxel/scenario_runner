# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================

import sys, time, random

import carla

from multisensors.utils.manual_control_global_funcs import find_weather_presets, get_actor_blueprints, get_actor_display_name
from multisensors.sensors.CollisionSensor import CollisionSensor
from multisensors.sensors.LaneInvasionSensor import LaneInvasionSensor
from multisensors.sensors.GnssSensor import GnssSensor
from multisensors.sensors.IMUSensor import IMUSensor
from multisensors.sensors.RadarSensor import RadarSensor 
from multisensors.displays.SensorManager import SensorManager


class World(object):
    def __init__(self, carla_world, hud, sensors, args):
        self.world = carla_world
        self.sync = args.sync
        self.actor_role_name = args.rolename

        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)

        # self.radar_sensor = None # unused
        # self.camera_manager = None # unused

        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.sensor_managers = None
        self.imu_sensor = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = args.filter
        self._actor_generation = args.generation
        self._gamma = args.gamma
        self.scenario_mode = args.scenario_mode if args.scenario_mode is not None else False
        self.restart()
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.show_vehicle_telemetry = False
        self.doors_are_open = False
        self.current_map_layer = 0
        self.map_layer_names = [
            carla.MapLayer.NONE,
            carla.MapLayer.Buildings,
            carla.MapLayer.Decals,
            carla.MapLayer.Foliage,
            carla.MapLayer.Ground,
            carla.MapLayer.ParkedVehicles,
            carla.MapLayer.Particles,
            carla.MapLayer.Props,
            carla.MapLayer.StreetLights,
            carla.MapLayer.Walls,
            carla.MapLayer.All
        ]

        self.sensor_managers = None # includes: camera, lidar, radar
        sensor_managers = []
        for sensor in sensors:
            sensor_man = SensorManager(
                carla_world,
                self.hud,
                sensor.get('type', None),
                sensor.get('name', None), 
                sensor.get('transform', None),
                self.player,
                sensor.get('options', None),
                sensor.get('grid', None)
            )
            if sensor['type'] == "GNSS":
                self.gnss_sensor = sensor_man.sensor
            else: # Camera, LiDAR, Radar
                sensor_managers.append(sensor_man)

        self.sensor_managers = sensor_managers


    def restart(self):
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        # Keep same camera config if the camera manager exists.
        # cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        # cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a random blueprint.
        blueprint = random.choice(get_actor_blueprints(self.world, self._actor_filter, self._actor_generation))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'true')
        # set the max speed
        if blueprint.has_attribute('speed'):
            self.player_max_speed = float(blueprint.get_attribute('speed').recommended_values[1])
            self.player_max_speed_fast = float(blueprint.get_attribute('speed').recommended_values[2])

        # Spawn the player.

        if not self.scenario_mode:    
            if self.player is not None:
                spawn_point = self.player.get_transform()
                spawn_point.location.z += 2.0
                spawn_point.rotation.roll = 0.0
                spawn_point.rotation.pitch = 0.0
                self.destroy()
                self.player = self.world.try_spawn_actor(blueprint, spawn_point)
                self.show_vehicle_telemetry = False
                self.modify_vehicle_physics(self.player)

        if self.scenario_mode:
            while self.player is None:
                print("Waiting for the ego vehicle...")
                time.sleep(1)
                possible_vehicles = list(self.world.get_actors().filter('vehicle.*'))
                for vehicle in possible_vehicles[::-1]:
                    if vehicle.attributes['role_name'] == self.actor_role_name:
                        print("Ego vehicle found")
                        self.player = vehicle
                        break
            
            self.player_name = self.player.type_id
        else:
            while self.player is None:
            
                if not self.map.get_spawn_points():
                    print('There are no spawn points available in your map/town.')
                    print('Please add some Vehicle Spawn Point to your UE4 scene.')
                    sys.exit(1)
                spawn_points = self.map.get_spawn_points()
                spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
                self.player = self.world.try_spawn_actor(blueprint, spawn_point)
                self.show_vehicle_telemetry = False
                self.modify_vehicle_physics(self.player)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        # self.gnss_sensor = GnssSensor(self.player, location=carla.Transform(carla.Location(x=1.0, z=2.8)))
        self.imu_sensor = IMUSensor(self.player)

        # self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        # self.camera_manager.transform_index = cam_pos_index
        # self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

        if self.sync:
            self.world.tick()
        else:
            self.world.wait_for_tick()

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def next_map_layer(self, reverse=False):
        self.current_map_layer += -1 if reverse else 1
        self.current_map_layer %= len(self.map_layer_names)
        selected = self.map_layer_names[self.current_map_layer]
        self.hud.notification('LayerMap selected: %s' % selected)

    def load_map_layer(self, unload=False):
        selected = self.map_layer_names[self.current_map_layer]
        if unload:
            self.hud.notification('Unloading map layer: %s' % selected)
            self.world.unload_map_layer(selected)
        else:
            self.hud.notification('Loading map layer: %s' % selected)
            self.world.load_map_layer(selected)

    def toggle_radar(self):
        if self.radar_sensor is None:
            self.radar_sensor = RadarSensor(self.player)
        elif self.radar_sensor.sensor is not None:
            self.radar_sensor.sensor.destroy()
            self.radar_sensor = None

    def flip_cameras(self):
        for sensor in self.sensor_managers:
            if sensor.type == 'RGBCamera':
                sensor.flip()

    def modify_vehicle_physics(self, actor):
        #If actor is not a vehicle, we cannot use the physics control
        try:
            physics_control = actor.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            actor.apply_physics_control(physics_control)
        except Exception:
            pass

    def tick(self, clock):
        if len(self.world.get_actors().filter(self.player_name)) < 1:
            return False
        self.hud.tick(self, clock)
        return True

    def render(self):
        # self.camera_manager.render(self.hud.display)
        self.hud.render()

    def destroy_sensors(self):
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        # if self.radar_sensor is not None:
        #     self.toggle_radar()

        sensors = [
            *self.sensor_managers,
            self.gnss_sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.imu_sensor.sensor]
            
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()

        if self.player is not None:
            self.player.destroy()