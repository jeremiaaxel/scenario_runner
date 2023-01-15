# ==============================================================================
# -- WorldSR ---------------------------------------------------------------------
# ==============================================================================

import time

from utils.manual_control_global_funcs import get_actor_display_name

from sensors.CollisionSensor import CollisionSensor
from sensors.LaneInvasionSensor import LaneInvasionSensor
from sensors.IMUSensor import IMUSensor
from displays.World import World

class WorldSR(World):
    restarted = False

    def restart(self):
        if self.restarted:
            return
        self.restarted = True

        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713

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

        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.imu_sensor = IMUSensor(self.player)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

        if self.sync:
            self.world.tick()
        else:
            self.world.wait_for_tick()

    def tick(self, clock):
        if len(self.world.get_actors().filter(self.player_name)) < 1:
            return False

        self.hud.tick(self, clock)
