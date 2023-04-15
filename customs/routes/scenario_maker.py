import os
import json
import carla
import random
import logging

from datetime import datetime
from argparse import ArgumentParser

from customs.configs.config import OUT_DIR
from customs.routes.available_scenarios import AvailableScenarios

from srunner.tools.route_parser import RouteParser
from srunner.tools.route_manipulation import interpolate_trajectory

fullfilename = os.path.join(OUT_DIR, "scenario_maker.log")
logging.basicConfig(filename=fullfilename, level=logging.INFO)
logger = logging.getLogger(__name__)

class ScenarioMaker(object):
    """
    Make scenario file in a route
    """
    def __init__(self, args) -> None:
        self._args = args
        self._client = carla.Client(args.host, int(args.port))
        if args.timeout:
            self.client_timeout = float(args.timeout)
        self._client.set_timeout(self.client_timeout)
        self._world = self._client.get_world()

    def _get_route_interpolated(self) -> list:
        if not self._args.route:
            logger.error("Only route-based scenario generation")
            return
        
        routes = self._args.route[0]
        single_route = None
        if len(self._args.route) > 1:
            single_route = self._args.route[1]
        route_configurations = RouteParser.parse_routes_file(routes, None, single_route=single_route)

        interpolated_routes = []
        for config in route_configurations:
            _, route = interpolate_trajectory(self._world, config.trajectory)
            interpolated_routes.append(route)

        return interpolated_routes
    
    def _construct_scenario(self, interpolated_routes, available_scenarios):
        this_map = "Town10HD_Opt"
        this_map_scenario = []

        for route in interpolated_routes:
            selected_scenarios = random.sample(available_scenarios, self._args.number_of_scenario_types)
            random.shuffle(selected_scenarios)

            n_points = len(route)
            n_chunks = n_points // len(selected_scenarios)
            curr_chunk = (0, n_chunks)
            for scenario_type in selected_scenarios:
                idx = random.randrange(curr_chunk[0], curr_chunk[1])
                wp_transform, _ = route[idx]

                if scenario_type is None:
                    continue

                this_map_scenario.append({ 
                    "available_event_configurations": [
                        {
                            "transform": {
                                "pitch": str(wp_transform.rotation.pitch),
                                "yaw": str(wp_transform.rotation.yaw),
                                "x": str(wp_transform.location.x),
                                "y": str(wp_transform.location.y),
                                "z": str(wp_transform.location.z)
                            }
                        }
                    ],
                    "scenario_type": str(scenario_type)
                })

                curr_chunk = (n_chunks, n_chunks + n_chunks)

        scenario = { 
            "available_scenarios": [
                {
                    this_map: this_map_scenario
                }
            ] 
        }
        return scenario

    def _get_scenario_types(self):
        return AvailableScenarios.get_all_scenarios()
    
    def generate_scenario(self) -> bool:
        result = True

        interpolated_routes = self._get_route_interpolated()
        scenario_types = self._get_scenario_types().keys()
        constructed_scenario_dict = self._construct_scenario(interpolated_routes, scenario_types)

        filename = self._args.filename
        if filename is None:
            filename = f"scenario_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        outdir = self._args.outdir
        if outdir is None:
            outdir = os.path.dirname(os.path.realpath(__file__))
            outdir = os.path.join(outdir, "out")

        os.makedirs(outdir, exist_ok=True)

        fullfilename = os.path.join(outdir, filename)
        with open(fullfilename, "w") as jsonfile:
            jsonfile.write(json.dumps(constructed_scenario_dict, indent=4))
            logger.info(f"Created scenario: {fullfilename}")

        return result
            

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1',
                        help='IP of the host server (default: localhost)')
    parser.add_argument('--port', default='2000',
                        help='TCP port to listen to (default: 2000)')
    parser.add_argument('--timeout', default="10.0",
                        help='Set the CARLA client timeout value in seconds')
    parser.add_argument('--sync', action='store_true',
                        help='Forces the simulation to run synchronously')
    parser.add_argument('--route', 
                        help='Run a route as a scenario (input: (route_file,scenario_file,[route id]))', nargs='+', type=str)
    parser.add_argument('--filename',
                        help="Result scenario filename", default=None)
    parser.add_argument('--outdir',
                        help="Result scenario filename (default to the same directory as this file)", default=None)
    parser.add_argument('--number-of-scenario-types', default=5,
                        help='Number of scenario types going to be implemented in a single route scenario')
    
    arguments = parser.parse_args()
    scenario_maker = ScenarioMaker(arguments)
    scenario_maker.generate_scenario()
    