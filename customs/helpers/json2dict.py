import json
from typing import Union

def json2dict(path_to_conf_file) -> Union[dict, None]:
    with open(path_to_conf_file) as json_file:
        return json.load(json_file)