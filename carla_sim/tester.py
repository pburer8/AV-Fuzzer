import carla
import time
import math
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../PythonAPI')))
from agents.navigation.behavior_agent import BehaviorAgent
import liability
import  tools
import simulation
import random
from collections import namedtuple
import yaml
from datetime import datetime
import argparse


def run(spawn_config, weather_config):
    tick_interval  = 0.05
    max_frames     = 200
    interval       = int(1.0/tick_interval)
    num_intervals  = max_frames//interval + 1

    npc1_behaviors = tools.generate_npc_behaviors(spawn_config['npc1'], num_intervals, extra_steer_perturb=True)
    npc2_behaviors = tools.generate_npc_behaviors(spawn_config['npc2'], num_intervals, extra_steer_perturb=True)

    result = simulation.run_simulation(
        spawn_config,
        weather_config,
        npc1_behaviors,
        npc2_behaviors,
        tick_interval=tick_interval,
        max_frames=max_frames
    )

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = 'Tester', description='Tester for the liability module')
    parser.add_argument('-w', '--weather', default='parameters/weather.yaml', type=str, metavar='path/to/weather.yaml')
    parser.add_argument('-s', '--spawn', default='parameters/spawn.yaml', type=str, metavar='path/to/spawn.yaml')
    parser.add_argument('-n', '--runs', default=20, type=int, metavar='number of runs')

    args = parser.parse_args()

    weather_config = tools.load_weather_yaml(args.weather)
    spawn_config  = tools.load_spawn_yaml(args.spawn)

    total = args.runs
    crashes = 0
    ego_faults = 0

    ego_crash_types = {}
    npc_crash_types = {}

    for i in range(total):
        print(f"--- RUN {i+1}/{total} ---\n")
        simulate = run(spawn_config, weather_config)

        if simulate.isHit:
            crashes += 1

        if simulate.isEgoFault[0]:
            ego_faults += 1
            if simulate.isEgoFault[1] in ego_crash_types:
                ego_crash_types[simulate.isEgoFault[1]] += 1
            else:
                ego_crash_types[simulate.isEgoFault[1]] = 1
        else:
            if simulate.isEgoFault[1] in npc_crash_types:
                npc_crash_types[simulate.isEgoFault[1]] += 1
            else:
                npc_crash_types[simulate.isEgoFault[1]] = 1
    
    crash_types = {}

    if ego_crash_types:
        crash_types['ego'] = ego_crash_types
    if npc_crash_types:
        crash_types['npc'] = npc_crash_types
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"./logs/testing/test_log_{ts}.yaml"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    f = open(log_path,'w')
    yaml.safe_dump({'file_name': args.spawn,
                    'results': {
                        'crashes': crashes,
                        'ego_faults': ego_faults,
                        'npc_faults': crashes - ego_faults,
                        'crash_type_distribution': crash_types
    }}, f, default_flow_style=False, sort_keys=False)
    f.close()

