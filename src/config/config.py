import os
import json

import src
from src import _ROOT
from src.utils import JSONObject


class AppConfig(JSONObject):
    def __init__(self):
        config_path = src.get_path('config', 'config.json')
        with open(config_path, 'r') as config_fp:
            _json = json.load(config_fp)
        JSONObject.__init__(self, _json)

        output_path = self.get('output_path', str)
        output_path = output_path.replace('<ROOT>', _ROOT, 1)
        self.output_path = os.path.normpath(output_path)
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

    def to_json_string(self) -> str:
        return json.dumps(
            self,
            default=lambda o: o.__dict__
        )

    def dump(self) -> None:
        json_obj = json.loads(self.to_json_string())
        config_path = src.get_path('config', 'config.json')
        with open(config_path, 'w+') as config_fp:
            json.dump(json_obj, config_fp)
            config_fp.truncate()


app_config = AppConfig()
