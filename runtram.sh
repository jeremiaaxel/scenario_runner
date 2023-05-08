#!/bin/sh

tram_route_file="./customs/routes/tram_routes.xml"
scenarios_file="./customs/routes/full_scenarios.json"
agent_file="./customs/autoagents/hils_agent.py"
agent_config_file="./customs/autoagents/configs/human_tram.json"
route_number=$1
is_debug=$2

(set -x; python3 scenario_runner.py \
            --route $tram_route_file $scenarios_file $route_number \
            --agent $agent_file $is_debug \
            --agentConfig $agent_config_file)
