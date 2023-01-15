#!/usr/bin/env python

from __future__ import print_function

# import sytem libraries
import glob, os, sys
import argparse, logging
from pathlib import Path

# import carla libraries
import carla, pygame

# import custom dependencies
from displays.HUD import HUD
from displays.World import World
from displays.WorldSR import WorldSR
from displays.KeyboardControl import KeyboardControl
from utils.get_sensors_json import get_sensors_json

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):
    world = None
    original_settings = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(20.0)

        sim_world = client.get_world()
        if args.sync:
            original_settings = sim_world.get_settings()
            settings = sim_world.get_settings()
            if not settings.synchronous_mode:
                settings.synchronous_mode = True
                settings.fixed_delta_seconds = 0.05
            sim_world.apply_settings(settings)

            traffic_manager = client.get_trafficmanager()
            traffic_manager.set_synchronous_mode(True)

        if args.autopilot and not sim_world.get_settings().synchronous_mode:
            print("WARNING: You are currently in asynchronous mode and could "
                  "experience some issues with the traffic simulation")

        '''
        CAMERA RGBA
        all located at front of the tram
        top: 0, 1, 2, 3, 4
        0, 4: 30 deg outward
        1, 2, 3: 0 deg

        bottom: 5, 6, 7
        5, 7: 30 deg outward
        6: 0 deg

        x-axis: vehicle length
        y-axis: vehicle width
        z-axis: vehicle height
        '''
        sensors = get_sensors_json(args.sensors_config)
        if sensors is None:
            print("ERROR: No sensors found in the sensors.json file")
            return
        grid_size = [
            max([sensor['grid'][0] for sensor in sensors if 'grid' in sensor]) + 1,
            max([sensor['grid'][1] for sensor in sensors if 'grid' in sensor]) + 1
        ]

        hud = HUD(args.width, args.height, grid_size=grid_size)
        world = World(sim_world, hud, sensors, args) if not args.scenario_mode else WorldSR(sim_world, hud, sensors, args)
        controller = KeyboardControl(world, args.autopilot)

        clock = pygame.time.Clock()
        while True:
            if args.sync:
                sim_world.tick()
            else:
                sim_world.wait_for_tick()
            clock.tick_busy_loop(60)
            if controller.parse_events(client, world, clock, args.sync):
                return
            world.tick(clock)
            world.render()

    finally:

        if original_settings:
            sim_world.apply_settings(original_settings)

        if (world and world.recording_enabled):
            client.stop_recorder()

        if world is not None:
            world.destroy()

        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--generation',
        metavar='G',
        default='2',
        help='restrict to certain actor generation (values: "1","2","All" - default: "2")')
    argparser.add_argument(
        '--rolename',
        metavar='NAME',
        default='hero',
        help='actor role name (default: "hero")')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    argparser.add_argument(
        '--sync',
        action='store_true',
        help='Activate synchronous mode execution')
    argparser.add_argument(
        '--keep_ego_vehicle',
        action='store_true',
        help='do not destroy ego vehicle on exit')
    argparser.add_argument(
        '--sensors-config',
        nargs=1,
        type=str,
        default=(Path(__file__).parent / 'sensors_config.json').resolve(),
        help='Path to sensors configuration file')
    argparser.add_argument(
        '--scenario-mode',
        action='store_true',
        help='Activate scenario mode execution')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()
