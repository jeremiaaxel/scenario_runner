from dataclasses import dataclass
import os
import sys
import json
from typing import Dict, List, Literal
import carla
import random
import logging

from datetime import datetime
from argparse import ArgumentParser

from srunner.scenarios.basic_scenario import BasicScenario

sys.path.append(os.getcwd())
from customs.scenario_maker.available_scenarios import AvailableScenarios

from srunner.tools.route_parser import RouteParser
from srunner.tools.route_manipulation import interpolate_trajectory

OUT_DIR = os.path.dirname(os.path.realpath(__file__))
OUT_DIR = os.path.join(OUT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)

fullfilename = os.path.join(OUT_DIR, "scenario_maker.log")
logging.basicConfig(filename=fullfilename, filemode="a", level=logging.INFO)
logger = logging.getLogger(__name__)

MAP_NAME = "Town10HD_Opt"


@dataclass
class ScenarioItem(object):
    x: float
    y: float
    z: float
    pitch: float
    yaw: float
    scenario_type: str


class ScenarioMaker(object):
    """
    Make scenario file in a route
    """

    def __init__(self, map_name, args) -> None:
        self._map_name = map_name
        self._args = args
        self._client = carla.Client(args.host, int(args.port))
        if args.timeout:
            self.client_timeout = float(args.timeout)
        self._client.set_timeout(self.client_timeout)
        self._world = self._client.get_world()
        self._selected_scenarios = dict()

        self._validation_occ_size = args.validation
        self._validation_mode = True if args.validation > 0 else False

    def _get_route_interpolated(self) -> list:
        if not self._args.route:
            logger.error("Only route-based scenario generation is supported")
            return

        route_filename = self._args.route[0]
        single_route = None
        if len(self._args.route) > 1:
            single_route = self._args.route[1]

        report = f"Creating scenario for {route_filename}"
        if single_route:
            report += f" at {single_route}"
        logger.info(report)

        route_configurations = RouteParser.parse_routes_file(
            route_filename, None, single_route=single_route
        )

        if len(route_configurations) == 0:
            logger.error("Route Configurations length is 0, something went wrong")

        interpolated_routes = []
        for config in route_configurations:
            _, route = interpolate_trajectory(self._world, config.trajectory)
            interpolated_routes.append(route)

        return interpolated_routes

    @staticmethod
    def __select_init_scenarios(background_selection_method="random"):
        """
        Selects the initialization scenarios from BACKGROUND_SCENARIOS in available_scenarios.
        """

        def select_from_options(
            options: Dict[str, BasicScenario],
            selection_method: Literal["all", "random", "none"] = "all",
            randsize: int = 1,
        ):
            """
            param:
                selection_method: the method used for selection: all, random, none
                randsize: the size of random. Must be used with random selection method
            """
            if selection_method == "none":
                return []

            selecteds = options.keys()
            if selection_method == "random":
                if randsize > len(options.keys()):
                    print(
                        f"Random size {randsize} is bigger the available options {len(options.keys())}."
                    )
                    print("Using options size instead.")
                    randsize = len(options.keys())
                selecteds = random.sample(options.keys(), randsize)

            # SpawnMixed xor these exceptions
            spawn_mixed_exceptions = ["SpawnAngkot", "SpawnBike", "SpawnActor"]
            if any(selected.startswith("SpawnMixed") for selected in selecteds):
                selecteds = [
                    selected
                    for selected in selecteds
                    if not any(
                        selected.startswith(pre_exception)
                        for pre_exception in spawn_mixed_exceptions
                    )
                ]
            return selecteds

        weather_scenarios = AvailableScenarios.get_weather_scenarios()
        time_scenarios = AvailableScenarios.get_time_scenarios()
        background_scenarios = AvailableScenarios.get_background_scenarios()

        init_scenarios = []
        init_scenarios.extend(select_from_options(time_scenarios, "random", 1))
        init_scenarios.extend(select_from_options(weather_scenarios, "random", 1))
        init_scenarios.extend(
            select_from_options(background_scenarios, background_selection_method)
        )
        return init_scenarios

    @staticmethod
    def __select_main_scenarios(
        number_of_scenarios: int, avoid_used=True, used_scenarios_key=[]
    ):
        all_scenarios = AvailableScenarios.get_all_scenarios()

        if avoid_used:
            logger.debug(f"All scenarios keys BEFORE filter: {all_scenarios.keys()}")
            all_scenarios = {
                k: v for k, v in all_scenarios.items() if k not in used_scenarios_key
            }
            logger.debug(f"Used scenarios keys: {used_scenarios_key}")
            logger.debug(f"All scenarios keys AFTER filter: {all_scenarios.keys()}")

        selected_scenarios = random.choices(all_scenarios.keys(), k=number_of_scenarios)
        random.shuffle(selected_scenarios)
        return selected_scenarios

    def __scenarios_selection(
        self, interpolated_routes
    ) -> Dict[int, Dict[int, ScenarioItem]]:
        """
        There are 2 groups of scenario:
         1. Init scenario defines the starting condition of the simulation.
            Init scenarios contains weather scenario, time scenario, and background scenario.
         2. Main scenario defines the scenarios during the simulation.
            Main scenario may contains all type of scenarios.
        """
        if self._validation_mode:
            return self.__validation_scenarios_selection(
                interpolated_routes, self._validation_occ_size
            )

        this_map_scenarios: Dict[int, List[ScenarioItem]] = dict()

        # scenario selections
        for route_idx, route in enumerate(interpolated_routes):
            this_route_scenarios: Dict[ScenarioItem] = {}

            # append init scenarios to the dictionary
            init_scenarios = self.__select_init_scenarios(
                background_selection_method=self._args.background_selection_method
            )
            logger.info(f"Init scenarios with length: {len(init_scenarios)}")
            wp_idx = 3
            for _, scenario_type in enumerate(init_scenarios):
                if wp_idx >= len(route):
                    logger.debug_s("Index greater than route size. Breaking")
                    break

                wp_transform, _ = route[wp_idx]
                this_route_scenarios[wp_idx] = ScenarioItem(
                    x=wp_transform.location.x,
                    y=wp_transform.location.y,
                    z=wp_transform.location.z,
                    pitch=wp_transform.rotation.pitch,
                    yaw=wp_transform.rotation.yaw,
                    scenario_type=str(scenario_type),
                )
                wp_idx += 2

            used_scenarios_key = [
                scenario_item.scenario_type
                for scenario_item in this_route_scenarios.values()
            ]

            # append main scenarios to the dictionary
            selected_scenarios = self.__select_main_scenarios(
                self._args.number_of_scenario_types,
                avoid_used=True,
                used_scenarios_key=used_scenarios_key,
            )
            logger.info(f"Main scenarios with length: {len(selected_scenarios)}")
            n_points = len(route)
            n_chunks = 0
            if len(selected_scenarios) > 0:
                n_chunks = n_points // len(selected_scenarios)
            curr_chunk = (wp_idx + 2, wp_idx + 2 + n_chunks)
            for scenario_type in selected_scenarios:
                wp_idx = random.randrange(curr_chunk[0], curr_chunk[1])
                if wp_idx >= len(route):
                    logger.debug_s("Index greater than route size. Breaking")
                    break

                wp_transform, _ = route[wp_idx]

                if scenario_type is None:
                    continue

                this_route_scenarios[wp_idx] = ScenarioItem(
                    x=wp_transform.location.x,
                    y=wp_transform.location.y,
                    z=wp_transform.location.z,
                    pitch=wp_transform.rotation.pitch,
                    yaw=wp_transform.rotation.yaw,
                    scenario_type=str(scenario_type),
                )

                curr_chunk = (curr_chunk[1], curr_chunk[1] + n_chunks)

            if self._args.crossings_percent:
                crossing_percentage = float(self._args.crossings_percent)

                logger.info(
                    f"Appending scenarios with crossings percentage: {crossing_percentage}"
                )
                crossing_scenarios = [
                    scen_key
                    for scen_key in AvailableScenarios.get_other_scenarios().keys()
                    if scen_key.lower().startswith("crossing")
                ]

                wp_idx = 0
                while wp_idx < len(route):
                    if wp_idx in this_route_scenarios.keys():
                        continue
                    if random.random() <= crossing_percentage:
                        continue

                    wp_transform, _ = route[wp_idx]
                    crossing_scen = random.choice(crossing_scenarios)
                    this_route_scenarios[wp_idx] = ScenarioItem(
                        x=wp_transform.location.x,
                        y=wp_transform.location.y,
                        z=wp_transform.location.z,
                        pitch=wp_transform.rotation.pitch,
                        yaw=wp_transform.rotation.yaw,
                        scenario_type=str(crossing_scen),
                    )

                    wp_idx += random.randint(12, 30)

            this_map_scenarios[route_idx] = this_route_scenarios

        return this_map_scenarios

    def __validation_scenarios_selection(self, interpolated_routes, occurences_each=1):
        """
        Construct scenarios for each scenario with n time occurence(s)
        Also use non background scenario(s) to minimize 'untangled' scenario(s).
        """

        def is_all_occurences_ok(
            scenario_occurences: Dict[str, int], occurences_size: int
        ) -> bool:
            """
            Checks if all occurences are occurences_size
            """
            unique_occ = set([occ for occ in scenario_occurences.values()])
            return len(unique_occ) == 1 and list(unique_occ)[0] == occurences_size

        logger.info(
            f"Generating scenario for validation with occurences size: {occurences_each}"
        )

        this_map_scenarios: Dict[int, List[ScenarioItem]] = dict()

        for route_idx, route in enumerate(interpolated_routes):
            all_scenario_occurences = {
                scenario_key: 0
                for scenario_key in AvailableScenarios.get_validation_scenarios().keys()
            }

            wp_idx = 3
            wp_out = False
            this_route_scenarios: Dict[ScenarioItem] = {}
            for scenario_type in all_scenario_occurences.keys():
                if wp_out:
                    break

                for _ in range(occurences_each):
                    if wp_idx >= len(route):
                        wp_out = True
                        break

                    wp_transform, _ = route[wp_idx]
                    this_route_scenarios[wp_idx] = ScenarioItem(
                        x=wp_transform.location.x,
                        y=wp_transform.location.y,
                        z=wp_transform.location.z,
                        pitch=wp_transform.rotation.pitch,
                        yaw=wp_transform.rotation.yaw,
                        scenario_type=str(scenario_type),
                    )
                    wp_idx += random.randint(12, 30)
                    all_scenario_occurences[scenario_type] += 1

            if not is_all_occurences_ok(all_scenario_occurences, occurences_each):
                logger.info("Scenario size is bigger than route's waypoints size")

            logger.info(
                f"Constructed validation scenario with: {all_scenario_occurences}"
            )
            this_map_scenarios[route_idx] = this_route_scenarios

        return this_map_scenarios

    def _construct_scenario(self, interpolated_routes: list) -> dict:
        """
        Function to construct a route scenario for each single scenario(s).
        """

        map_scenarios = self.__scenarios_selection(interpolated_routes)
        map_scenarios_json = []

        for _, route_scenarios in map_scenarios.items():
            for _, route_scenario in route_scenarios.items():
                map_scenarios_json.append(
                    {
                        "available_event_configurations": [
                            {
                                "transform": {
                                    "pitch": str(route_scenario.pitch),
                                    "yaw": str(route_scenario.yaw),
                                    "x": str(route_scenario.x),
                                    "y": str(route_scenario.y),
                                    "z": str(route_scenario.z),
                                }
                            }
                        ],
                        "scenario_type": str(route_scenario.scenario_type),
                    }
                )

        scenario = {"available_scenarios": [{self._map_name: map_scenarios_json}]}
        return scenario

    def generate_scenario(self) -> bool:
        result = True

        interpolated_routes = self._get_route_interpolated()

        if len(interpolated_routes) == 0:
            logger.error("Interpolated routes length is 0, something went wrong")
        else:
            logger.info("Interpolated routes created ")

        constructed_scenario_dict = self._construct_scenario(interpolated_routes)

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


def background_selection_mapper(no_init, is_all):
    if no_init:
        return "none"
    return "all" if is_all else "random"


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--host", default="127.0.0.1", help="IP of the host server (default: localhost)"
    )
    parser.add_argument(
        "--port", default="2000", help="TCP port to listen to (default: 2000)"
    )
    parser.add_argument(
        "--timeout",
        default="10.0",
        help="Set the CARLA client timeout value in seconds",
    )
    parser.add_argument(
        "--sync", action="store_true", help="Forces the simulation to run synchronously"
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="Disables initialization scenarios (no scenarios run on earliest waypoints)",
    )
    parser.add_argument(
        "--background-all",
        action="store_true",
        help="Uses all available background scenarios on init",
    )
    parser.add_argument(
        "--validation",
        help="Uses all available background scenarios with occurences",
        default=-1,
        const=1,
        nargs="?",
        type=int,
    )
    parser.add_argument(
        "--crossings-percent",
        default=0.5,
        type=float,
        help="Percentage of adding pedestrian crossing scenarios through the route",
    )
    parser.add_argument(
        "--route",
        help="Run a route as a scenario (input: (route_file,route id))",
        nargs="+",
        type=str,
    )
    parser.add_argument("--filename", help="Result scenario filename", default=None)
    parser.add_argument(
        "--outdir",
        help="Result scenario filename (default to the same directory as this file)",
        default=None,
    )
    parser.add_argument(
        "--number-of-scenario-types",
        default=5,
        type=int,
        help="Number of scenario types going to be implemented in a single route scenario",
    )

    arguments = parser.parse_args()
    arguments.background_selection_method = background_selection_mapper(
        arguments.no_init, arguments.background_all
    )
    scenario_maker = ScenarioMaker(MAP_NAME, arguments)
    scenario_maker.generate_scenario()
