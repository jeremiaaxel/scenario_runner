# Route-based Scenario Runner for Tram
Created by [jeremiaaxel](https://github.com/jeremiaaxel), modified from [ScenarioRunner v0.9.12](https://github.com/carla-simulator/scenario_runner/tree/v0.9.12)

## How to Run - Specific for RISPRO 2023
> :information_source: In commands, `[]` means optional and `()` means required

> :information_source: **Ordered list means command order** while **unordered list means optional to choose one** of the commands.
1. Use SILS computer.
2. Open terminal.
3. Change directory to the project folder
    ```bash
    cd ~/jeremia/custom-scenario_runner/
    ```
4. Prepare environment
    1. Activate conda environment
        ```bash
        conda activate j_carla_py38
        ```
    2. Setup environment variables
        ```bash
        source ./setup-env.sh
        ```
5. Run the Scenario Runner
    - Use convenience script 
        ```bash
        ./runtram.sh [repetition] [route number] [options]
        ```
        > :information_source: You can open the convenience script to learn more about the actual command to run the program.
        
        example:
        ```bash
        ./runtram.sh 2 1 --output --file
        ```
        The script above will run scenario runner for 2 repetitions in route 1 and write the result of each run into a file.
    - Use the actual command
        ```bash
        python scenario_runner.py --route (route file) (scenario file) [route number] --agent (agent file)
        ```

        example:
        ```bash
        python scenario_runner.py --route ./customs/routes/tram_routes.xml ./customs/routes/full_scenarios.json --agent ./customs/autoagents/human_tram_agent.py
        ```

6. To stop the program, press `Ctrl+c` in the terminal.