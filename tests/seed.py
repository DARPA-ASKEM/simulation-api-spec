from glob import glob
import json
import os
import logging

import requests

from auth import auth_session
from utils import create_project, add_asset

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TDS_URL = os.environ.get("TDS_URL", "http://hmi-server:3000")

if __name__ == "__main__":
    # Get project ID from environment
    project_id = os.environ.get("PROJECT_ID")

    if project_id:
        logging.info(f"Found project ID in environment: {project_id}")
        proj_resp = auth_session().get(f"{TDS_URL}/projects/{project_id}")
        if proj_resp.status_code == 404:
            raise Exception(
                f"Project ID {project_id} does not exist in TDS at {TDS_URL}"
            )

        # if the project exists, remove all simulations from it
        types = ["simulations"]
        sim_resp = auth_session().get(
            f"{TDS_URL}/projects/{project_id}/assets", params={"types": types}
        )
        if sim_resp.status_code >= 300:
            raise Exception(
                f"Failed to check project for existing simulations: {sim_resp.status_code}: {sim_resp.json()}"
            )
        else:
            logging.info(f"Sim response: {sim_resp.json()}")
            for sim in sim_resp.json().get("simulations", []):
                sim_id = sim["id"]
                logging.info(f"Deleting {sim_id} from project {project_id}")
                del_resp = auth_session().delete(
                    f"{TDS_URL}/projects/{project_id}/assets/SIMULATION/{sim_id}"
                )
                if del_resp.status_code >= 300:
                    logging.info(f"Failed to delete simulation {sim_id}")
    # if it does not exist, create it
    else:
        project_id = create_project()
        logging.info(
            f"No project ID found in environment. Created project with ID: {project_id}"
        )

    with open("project_id.txt", "w") as f:
        f.write(f"{project_id}")

    model_configs = glob("./data/models/*.json")
    for config_path in model_configs:
        obj = json.load(open(config_path, "rb"))
        if "configuration" in obj:
            config = obj
            model = config["configuration"]
        else:
            model = obj
            config = {
                "name": model["header"]["name"],
                "description": model["header"]["description"],
                "configuration": model,
            }
        model_response = auth_session().post(
            TDS_URL + "/models",
            json=model,
            headers={"Content-Type": "application/json"},
        )
        if model_response.status_code >= 300:
            raise Exception(
                f"Failed to POST model ({model_response.status_code}): {config['id']}"
            )
        else:
            add_asset(model_response.json()["id"], "MODEL", project_id)

        config["model_id"] = model_response.json()["id"]
        config_response = auth_session().post(
            TDS_URL + "/model_configurations",
            json=config,
            headers={"Content-Type": "application/json"},
        )

    datasets = glob("./data/datasets/*.csv")
    for filepath in datasets:
        filename = filepath.split("/")[-1]
        dataset_name = filename.split(".")[0]
        dataset = {"name": dataset_name, "file_names": [filename]}
        dataset_response = auth_session().post(
            TDS_URL + "/datasets",
            json=dataset,
            headers={"Content-Type": "application/json"},
        )
        dataset_id = ""
        if dataset_response.status_code >= 300:
            raise Exception(
                f"Failed to POSt dataset ({dataset_response.status_code}): {dataset['name']}"
            )
        else:
            dataset_id = dataset_response.json()["id"]
            add_asset(dataset_id, "DATASET", project_id)

        url_response = auth_session().get(
            TDS_URL + f"/datasets/{dataset_id}/upload-url",
            params={"filename": filename},
        )
        upload_url = url_response.json()["url"]
        with open(filepath, "rb") as file:
            auth_session().put(upload_url, file)
