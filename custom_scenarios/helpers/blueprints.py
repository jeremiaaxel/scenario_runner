
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


def create_blueprints_by_attribute(attribute_name: str, attribute_value, model_name: str = "*", model_exceptions: list = []):
    blueprints = CarlaDataProvider._blueprint_library.filter(model_name)
    blueprints = [bp for bp in blueprints if bp.id not in model_exceptions]
    if type(attribute_value) == int:
        blueprints = [bp for bp in blueprints if int(bp.get_attribute(attribute_name)) == attribute_value]
    else:
        blueprints = [bp for bp in blueprints if bp.get_attribute(attribute_name) == attribute_value]
    return blueprints