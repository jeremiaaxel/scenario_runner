#!/bin/bash

: '
Bash script to run the tram testing simulation.
! Make sure the CARLA server is up and running.
'

display_help() {
  echo "Bash script to run the tram testing simulation" >&2
  echo
  echo "  --help, -h                  print this help message"
  echo "  --agent-mode, -am           which agent controls the tram. (\"human\", \"sils\", \"hils\" [default])"
  echo "  --scenario-mode, -sm        which scenario to use. (\"none\", \"noscenario\", \"test\", \"req\", \"request\", \"random\" [default])"
  echo "  --repetition, -r            how much repetition. default: 1"
  echo "  --route-number, -rn         which route number to use (\"1\" [default], \"2\")"
  echo "  --scenario-base-size, -sbs  how much number of subscenario to generate scenario. Has to be used with \"random\" scenario mode. default: 0"
}

# CONFIGURATIONS - START
tram_route_file="./customs/routes/tram_routes.xml"

agent_config_file="./customs/autoagents/configs/human_tram.json"

scenario_runner="./scenario_runner.py"
scenario_maker="./customs/scenario_maker/scenario_maker.py"

# randomized generated scenario (default)
declare -A defined_scenario_files
# "test"
defined_scenario_files[test]="./customs/constructed_scenarios/test_scenarios.json"
# "none" | "noscenario"
defined_scenario_files[none]="./customs/constructed_scenarios/no_scenarios.json"
# "req" | "request"
defined_scenario_files[req]="./customs/constructed_scenarios/req_scenarios.json"
# "reg" | "regression"
defined_scenario_files[reg]="./customs/constructed_scenarios/reg_scenarios.json"
# "defined"
defined_scenario_files[defined]="./customs/constructed_scenarios/defined_scenarios_<NUM>.json"

declare -A defined_agent_files
# "hils" (default) 
defined_agent_files[hils]="./customs/autoagents/hils_agent.py"
# "sils"
defined_agent_files[sils]="./customs/autoagents/sils_agent.py"
# "human"
defined_agent_files[human]="./customs/autoagents/human_tram_agent.py"
# CONFIGURATIONS - END

# DEFAULT ARGUMENTS - START
agent_mode="hils"
agent_file=${defined_agent_files[$agent_mode]}

generate_scenario=true
scenario_mode="generate"
scenario_file=""

repetition="1"
route_number="1"
scenario_base_size="0"
is_help=false
# DEFAULT ARGUMENTS - END

# FUNCTIONS - START
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
    "reg"|"regression")
      scenario_mode="reg"
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
  # Exact scenario
  if [[ -n ${defined_scenario_files[$scenario_mode]} ]]; then
    generate_scenario=false
    scenario_file=${defined_scenario_files[$scenario_mode]};
  # Generation
  else
    echo "Scenario mode not found, using default (random)"
    generate_scenario=true
    scenario_file=""
  fi
}
# FUNCTIONS - END

# MAIN PROGRAM
## Extract user arguments 
SCENARIORUNNER_ARGS=()
RUNTRAM_ARGS=()
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
    -sbs|--scenario-base-size)
      scenario_base_size="$2"
      shift # past argument
      shift # past value
      ;;
    --validation)
      RUNTRAM_ARGS+=("$1")
      shift # past argument
      ;;
    --background-all)
      RUNTRAM_ARGS+=("$1")
      shift # past argument
      ;;
    -h|--help)
      is_help=true
      shift
      ;;
    # -*|--*)
    #   echo "Unknown option $1"
    #   exit 1
    #   ;;
    *)
      SCENARIORUNNER_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
scenariorunner_args="${SCENARIORUNNER_ARGS[*]}"
runtram_args="${RUNTRAM_ARGS[*]}"

# map agent mode to agent file
mapAgentMode

# map scenario mode to scenario file/generation
standardizeScenarioMode
mapScenarioMode

if [ $is_help = true ]; then
  display_help
  exit 0
fi

# print summary
echo "RUNTRAM: Autonomous Tram Testing Module"
echo "Agent used: \"$agent_mode\" : \"$agent_file\""
echo "Scenario mode: \"$scenario_mode\""
if [ $generate_scenario = true ]; then
  echo "Using scenario generation"
else
  echo "Using scenario: \"$scenario_file\""
fi

# repetitions
for (( i=1 ; i<=$repetition ; i++ )); do
    echo "#-repetition: $i"

    # SCENARIO MAKING
    if [ $generate_scenario = true ]; then
      scenario_file="scenario_repetition_$i.json"
      n_scenario_types=$(($scenario_base_size - 1 + $i));
      (set -x; python3 $scenario_maker \
                    --route $tram_route_file $route_number \
                    --filename $scenario_file \
                    --number-of-scenario-types $n_scenario_types \
                    --crossings-percent 0.5 \
                    $runtram_args)
      scenario_file="customs/scenario_maker/out/$scenario_file"
    fi

    # replace <NUM> with current repetition (for defined dynamic scenarios)
    scenario_file="${scenario_file/<NUM>/$i}"

    # SCENARIO RUNNING
    echo "Runtram using $scenario_file scenario";
    (set -x; python3 $scenario_runner \
                --route $tram_route_file $scenario_file $route_number \
                --agent $agent_file \
                --agentConfig $agent_config_file \
                $scenariorunner_args)

done
echo "Done"
