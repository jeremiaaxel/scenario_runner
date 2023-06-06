import re
import carla
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


def create_blueprints_by_attribute(attribute_name: str, attribute_value, model_name: str = "*", model_exceptions: list = []):
    blueprints = CarlaDataProvider._blueprint_library.filter(model_name)
    blueprints = [bp for bp in blueprints if bp.id not in model_exceptions]
    blueprints = [bp for bp in blueprints if bp.has_attribute(attribute_name)]
    if type(attribute_value) == int:
        blueprints = [bp for bp in blueprints if int(bp.get_attribute(attribute_name)) == attribute_value]
    else:
        blueprints = [bp for bp in blueprints if bp.get_attribute(attribute_name) == attribute_value]
    return blueprints


def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []

def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

def freeze_vehicle(vehicle):
    """
    Sets the vehicle to stop and disable physics
    """
    vehicle.set_autopilot(False)

def freeze_vehicles(vehicles):
    for vehicle in vehicles:
        freeze_vehicle(vehicle)

def freeze_pedestrian(ai_controller):
    ai_controller.stop()
    
def freeze_pedestrians(ai_controllers):
    for ai_controller in ai_controllers:
        freeze_pedestrian(ai_controller)

def start_ai_controller(ai_controller):
    ai_controller.start()

def start_ai_controllers(ai_controllers):
    for ai_controller in ai_controllers:
        start_ai_controller(ai_controller)
        
def set_location_ai_controller(ai_controller, start=False):
    target_location = CarlaDataProvider.get_world().get_random_location_from_navigation()
    ai_controller.go_to_location(target_location)
    if start:
        start_ai_controller(ai_controller)

def set_location_ai_controllers(ai_controllers, start=False):
    for ai_controller in ai_controllers:
        set_location_ai_controller(ai_controller, start=start)

def generate_walker_spawn_points(world, amount):
    spawn_points = []
    max_tries = 5
    for i in range(amount):
        spawn_point = carla.Transform()
        location = world.get_random_location_from_navigation()

        # re-get if location is already in spawn points to avoid collision on spawn
        tries = 0
        while location in spawn_points:
            if tries >= max_tries:
                break

            location = world.get_random_location_from_navigation()
            tries += 1

        if location:
            spawn_point.location = location
            spawn_points.append(spawn_point)
    return spawn_points

def hide_actor(actor, underground_z=500, freeze=False):
    location = actor.get_location()
    uground_location = carla.Location(location.x,
                                        location.y,
                                        location.z - underground_z)
    actor.set_simulate_physics(False)
    actor.set_location(uground_location)

    if freeze and isinstance(actor, carla.Vehicle):
        freeze_vehicle(actor)

def hide_actors(actors, underground_z=500, freeze=False):
    for actor in actors:
        hide_actor(actor, underground_z=underground_z, freeze=freeze)