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
    vehicle.set_simulate_physics(enabled=False)

def freeze_vehicles(vehicles):
    for vehicle in vehicles:
        freeze_vehicle(vehicle)