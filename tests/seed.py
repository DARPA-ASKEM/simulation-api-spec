from glob import glob
import json

import requests

TDS_URL = os.environ.get("TDS_URL", "http://data-service")


model_configs = glob("./data/models/*.json")
for config_path in moel_configs:
    config = json.load(config)
    model = config["configuration"]
    model_response = requests.post(TDS_URL + "/models", data=model)
    config_response = requests.post(TDS_URL + "/model_configurations", data=config)
    


dataset = {
    "name": "name"
}


model = {
    
}