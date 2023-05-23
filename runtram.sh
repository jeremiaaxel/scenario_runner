#!/bin/bash

tram_route_file="./customs/routes/tram_routes.xml"

agent_config_file="./customs/autoagents/configs/human_tram.json"

scenario_runner="./scenario_runner.py"
scenario_maker="./customs/scenario_maker/scenario_maker.py"


declare -A defined_scenario_files
defined_scenario_files[test]="./customs/routes/test_scenarios.json"
defined_scenario_files[none]="./customs/routes/no_scenarios.json"
defined_scenario_files[req]="./customs/routes/req_scenarios.json"

declare -A defined_agent_files
defined_agent_files[hils]="./customs/autoagents/hils_agent.py"
defined_agent_files[sils]="./customs/autoagents/sils_agent.py"
defined_agent_files[human]="./customs/autoagents/human_tram_agent.py"

# ARGUMENTS
## Default Arguments
agent_mode="hils"
agent_file=${defined_agent_files[$agent_mode]}

random_scenario=true
scenario_mode=""
scenario_file=""

repetition="1"
route_number="1"
scenario_base_size="0"

## EXTRACT ARGUMENTS
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--repetition)
      repetition="$2"
      shift # past argument
      shift # past value
      ;;
    -rn|--route-number)
      route_number="$2"
      shift # past argument
      shift # past value
      ;;
    -am|--agent-mode)
      agent_mode="$2"
      shift # past argument
      shift # past value
      ;;
    -sm|--scenario-mode)
      scenario_mode="$2"
      shift # past argument
      shift # past value
      ;;
    -sm|--scenario-base-size)
      scenario_base_size="$2"
      shift # past argument
      shift # past value
      ;;
    # -*|--*)
    #   echo "Unknown option $1"
    #   exit 1
    #   ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
rest="${POSITIONAL_ARGS[*]}"


function mapAgentMode() {
  # Agent Mode
  if [[ -n ${defined_agent_files[$agent_mode]} ]]; then
    agent_file=${defined_agent_files[$agent_mode]};
  else
    echo "Agent mode not found, using default (hils)"
    agent_file=${defined_agent_files[hils]};
  fi
}

function standardizeScenarioMode() {
  case $scenario_mode in 
    "req"|"request")
      scenario_mode="req"
      ;;
    "none"|"noscenario")
      scenario_mode="none"
      ;;
    *)
      ;;
  esac
}

function mapScenarioMode() {
  # Scenario Generation Mode
  if [[ -n ${defined_scenario_files[$scenario_mode]} ]]; then
    random_scenario=false
    scenario_file=${defined_scenario_files[$scenario_mode]};
  else
    echo "Scenario mode not found, using default (random)"
    random_scenario=true
    scenario_file=""
  fi
}

mapAgentMode

standardizeScenarioMode
mapScenarioMode

echo "Agent used: $agent_file"
if [ $random_scenario = true]; then
  echo "Using random scenario generation"
else
  echo "Using scenario: $scenario_file"
fi

for (( i=1 ; i<=$repetition ; i++ )); do
    echo "#-repetition: $i"

    # SCENARIO MAKING
    if [ $random_scenario = true ]; then
      scenario_file="scenario_repetition_$i.json"
      n_scenario_types=$(($scenario_base_size + $i));
      (set -x; python3 $scenario_maker \
                    --route $tram_route_file $route_number \
                    --filename $scenario_file \
                    --number-of-scenario-types $n_scenario_types)
      scenario_file="customs/scenario_maker/out/$scenario_file"
    fi

    # SCENARIO RUNNING
    echo "Runtram using $scenario_file scenario";
    (set -x; python3 $scenario_runner \
                --route $tram_route_file $scenario_file $route_number \
                --agent $agent_file \
                --agentConfig $agent_config_file \
                $rest)

done
echo "Done"
