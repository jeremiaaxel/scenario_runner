import subprocess

from argparse import ArgumentParser

TRAM_ROUTE_FILE = "./customs/routes/tram_routes.xml"
AGENT_FILE = "./customs/autoagents/hils_agent.py"
AGENT_CONFIG_FILE = "./customs/autoagents/configs/human_tram.json"

SCENARIO_RUNNER = "./scenario_runner.py"
SCENARIO_MAKER = "./customs/scenario_maker/scenario_maker.py"

def main(args):
    for i in range(args.repetition):
        repetition_num = i+1
        print(f"Repetition-{repetition_num}")
        # scenario maker
        scenario_filename = f"scenario_repetition_{repetition_num}.json"
        n_scenarios = i+1
        if not args.reuse_scenario:
            scenario_make_command = ["python3", SCENARIO_MAKER,
                                        "--route", TRAM_ROUTE_FILE, f"{args.route_number}",
                                        "--filename", scenario_filename,
                                        "--number-of-scenario-types", f"{n_scenarios}"]
            print(' '.join(scenario_make_command))
            result = subprocess.run(scenario_make_command, stdout=subprocess.PIPE)
            result.stdout.decode('utf-8')
            print(f"Created scenario")

        # scenario runner
        scenario_filename = f"customs/scenario_maker/out/{scenario_filename}"
        print(f"Runtram using {scenario_filename} scenario")
        scenario_run_command = ["python3", SCENARIO_RUNNER,
                                "--route", TRAM_ROUTE_FILE, scenario_filename, f"{args.route_number}",
                                "--agent", AGENT_FILE, "--agentConfig", AGENT_CONFIG_FILE]
        if args.other_options is not None:
            scenario_run_command.append(args.other_options)
        print(' '.join(scenario_run_command))
        result = subprocess.run(scenario_run_command, stdout=subprocess.PIPE)
        result.stdout.decode('utf-8')
        
    print(f"Done running {args.repetition} scenarios. Simulation results in 'out/results'")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--repetition", "-r",
                        help="How many times the scenario will be repeated",
                        type=int, default=1)
    parser.add_argument("--route-number", "-rn",
                        help="Which route number will be used",
                        type=int, default=1)
    parser.add_argument("--write-result", "-wr",
                        help="Writes the result of the simulation to file in out/results/",
                        action="store_true", default=False)
    parser.add_argument("--other-options", "-oo",
                        help="Use other options that is not specified in the ArgumentParser",
                        nargs="*")
    parser.add_argument("--reuse-scenario", "-rs",
                        help="Skips scenario making. Reuse previously created scenario",
                        action="store_true", default=False)
    arguments = parser.parse_args()
    main(args=arguments)