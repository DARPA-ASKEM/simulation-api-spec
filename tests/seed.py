from glob import glob
import json

import requests

TDS_URL = os.environ.get("TDS_URL", "http://data-service")

model_configs = glob("./data/models/*.json")
for config_path in model_configs:
    config = json.load(config)
    model = config["configuration"]
    model_response = requests.post(TDS_URL + "/models", data=model)
    if model_response >= 300:
        raise Exception(f"Failed to PUT model: {config["id"]}")
    config["model_id"] = model_response.json()["id"]
    config_response = requests.post(TDS_URL + "/model_configurations", data=config)
    if config_response >= 300:
        raise Exception(f"Failed to PUT config: {config["id"]}")

model_configs = glob("./data/datasetss/*.csv")
for filepath in datasets:
    filename = filepath.split("/")[-1]
    dataset_name = filename.split(".")[0]
    dataset = {
        "id": dataset_name,
        "name": dataset_name,
        "file_names": [
            filename
        ]
    }
    dataset_response = requests.post(TDS_URL + "/dataset", data=dataset)
    if dataset_response >= 300:
        raise Exception(f"Failed to PUT dataset: {dataset["name"]}")
    url_response = requests.get(TDS_URL + f"/dataset/{dataset_name}/upload-url", params={"filename": filename})
    upload_url = url_response.json()["url"]
    with open(filepath, "rb") as file:
        requests.put(upload_url, file)
        