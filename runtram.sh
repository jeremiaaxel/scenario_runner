#!/bin/bash

tram_route_file="./customs/routes/tram_routes.xml"
agent_file="./customs/autoagents/human_tram_agent.py"
agent_config_file="./customs/autoagents/configs/human_tram.json"
repetition=$1
route_number=$2
is_debug=$3

scenarios_file="./customs/routes/test_scenarios.json"

for (( i=1 ; i<=$repetition ; i++ ));
do
    echo "#-repetition: $i"
    (set -x; python3 scenario_runner.py \
                --route $tram_route_file $scenarios_file $route_number \
                --agent $agent_file $is_debug \
                --agentConfig $agent_config_file)
done
echo "Done"