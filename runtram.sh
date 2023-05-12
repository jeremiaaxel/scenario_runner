#!/bin/bash

tram_route_file="./customs/routes/tram_routes.xml"
agent_file="./customs/autoagents/human_tram_agent.py"
agent_config_file="./customs/autoagents/configs/human_tram.json"

scenario_runner="./scenario_runner.py"
scenario_maker="./customs/scenario_maker/scenario_maker.py"

args="$*"
repetition=$1
route_number=$2
rest=${args[@]:3}

scenarios_file="./customs/routes/test_scenarios.json"

for (( i=1 ; i<=$repetition ; i++ )); do
    echo "#-repetition: $i"
    scenario_filename="scenario_repetition_$i.json"
    n_scenario_types=$((10-$i));
    (set -x; python3 $scenario_maker \
                  --route $tram_route_file $route_number \
                  --filename $scenario_filename \
                  --number-of-scenario-types $n_scenario_types)
    scenario_filename="customs/scenario_maker/out/$scenario_filename"
    echo "Runtram using $scenario_filename scenario";
    (set -x; python3 $scenario_runner \
                --route $tram_route_file $scenario_filename $route_number \
                --agent $agent_file $rest \
                --agentConfig $agent_config_file)
done
echo "Done"