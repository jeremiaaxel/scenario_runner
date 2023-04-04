#!/bin/sh

tram_route_file="./custom_scenarios/routes/tram_routes.xml"
scenarios_file="./custom_scenarios/routes/full_scenarios.json"
agent_file="./custom_scenarios/autoagents/human_tram_agent.py"
route_number=$1
is_debug=$2

(set -x; python scenario_runner.py --route $tram_route_file $scenarios_file $route_number --agent $agent_file $is_debug)
