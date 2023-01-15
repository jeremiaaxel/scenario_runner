import logging

def update_vehicle_lights_ignore(world, traffic_manager, vehicles_list, disobeyness):
    all_vehicle_actors = world.get_actors(vehicles_list)
    for actor in all_vehicle_actors:
        traffic_manager.ignore_lights_percentage(actor, disobeyness)

    logging.info(f"Setting vehicle with traffic lights disobeyness: {disobeyness}")
    return traffic_manager

def update_vehicle_signs_ignore(world, traffic_manager, vehicles_list, disobeyness):
    all_vehicle_actors = world.get_actors(vehicles_list)
    for actor in all_vehicle_actors:
        traffic_manager.ignore_signs_percentage(actor, disobeyness)

    logging.info(f"Setting vehicle with traffic signs disobeyness: {disobeyness}")
    return traffic_manager

def update_vehicle_vehicles_collision_ignore(world, traffic_manager, vehicles_list, disobeyness):
    all_vehicle_actors = world.get_actors(vehicles_list)
    for actor in all_vehicle_actors:
        traffic_manager.ignore_vehicles_percentage(actor, disobeyness)

    logging.info(f"Setting vehicle with vehicles collision disobeyness: {disobeyness}")
    return traffic_manager

def update_vehicle_walkers_collision_ignore(world, traffic_manager, vehicles_list, disobeyness):
    all_vehicle_actors = world.get_actors(vehicles_list)
    for actor in all_vehicle_actors:
        traffic_manager.ignore_walkers_percentage(actor, disobeyness)

    logging.info(f"Setting vehicle with walkers collision disobeyness: {disobeyness}")
    return traffic_manager