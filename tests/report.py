import os
import json
import logging
from time import sleep, time
from datetime import datetime
from collections import defaultdict
from urllib.parse import urljoin

import boto3
import requests

from auth import auth_session
from utils import add_asset
from workflow import workflow_builder, generate_workflow

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TDS_URL = os.environ.get("TDS_URL", "http://hmi-server:3000")
PYCIEMSS_URL = os.environ.get("PYCIEMSS_URL", "http://pyciemss-api:8000")
SCIML_URL = os.environ.get("SCIML_URL", "http://sciml-service:8080")
BUCKET = os.environ.get("BUCKET", None)
UPLOAD = os.environ.get("UPLOAD", "FALSE").lower() == "true"

PROJECT_ID = os.environ.get("PROJECT_ID", None)


def eval_integration(service_name, endpoint, request):
    start_time = time()
    is_success = False
    base_url = PYCIEMSS_URL if service_name == "pyciemss" else SCIML_URL
    kickoff_request = requests.post(
        f"{base_url}/{endpoint}",
        json=request,
        headers={"Content-Type": "application/json"},
    )
    logging.info(
        f"Kicked request: {kickoff_request.status_code} {kickoff_request.text}"
    )
    if kickoff_request.status_code < 300:
        simulation_id = kickoff_request.json()["simulation_id"]
        logging.info(f"Simulation ID: {simulation_id}")
        get_status = lambda: requests.get(f"{base_url}/status/{simulation_id}").json()[
            "status"
        ]
        while get_status() in ["queued", "running"]:
            sleep(1)
        if get_status() == "complete":
            logging.info(f"Completed status on simulation: {simulation_id}")
            is_success = True
            # Add artifacts from simulations to TDS depending on what test is being run:
            # 1) Simulation in TDS
    return {
        "Integration Status": is_success,
        "Execution Time": time() - start_time,
    }


def add_workflow(workflow_payload):
    if workflow_payload is None:
        logging.info("No workflow payload provided, not making request")
        return
    workflow_response = auth_session().post(
        TDS_URL + "/workflows",
        json=workflow_payload,
        headers={"Content-Type": "application/json"},
    )

    workflow_id = None
    if workflow_response.status_code >= 300:
        raise Exception(
            f"Failed to post workflow ({workflow_response.status_code} {workflow_response.text})"
        )
    else:
        logging.info(
            f"Workflow created/updated with ID: {workflow_response.json().get('id')}"
        )

        if PROJECT_ID:
            project_id = PROJECT_ID
        else:
            try:
                with open("project_id.txt", "r") as f:
                    project_id = f.read()
            except:
                raise Exception(
                    "No PROJECT_ID found in environment and no project_id.txt file found"
                )

        workflow_id = workflow_response.json()["id"]
        add_asset(workflow_id, "WORKFLOW", project_id)

    return workflow_id


def update_workflow(workflow_id, workflow_payload):
    if workflow_payload is None:
        logging.info("No workflow payload provided, not making request")
        return
    workflow_response = auth_session().put(
        TDS_URL + f"/workflows/{workflow_id}",
        json=workflow_payload,
        headers={"Content-Type": "application/json"},
    )

    if workflow_response.status_code >= 300:
        raise Exception(
            f"Failed to update workflow ({workflow_response.status_code} {workflow_response.text})"
        )
    else:
        logging.info(
            f"Workflow updated with ID: {workflow_id}"
        )

    return workflow_response.json()


def gen_report():
    def get_version(base_url):
        response = requests.get(urljoin(base_url, "health"))
        if response.status_code < 300:
            return response.json()["git_sha"]
        else:
            return f"UNAVAILABLE: {response.status_code}"

    if PROJECT_ID:
        project_id = PROJECT_ID
    else:
        try:
            with open("project_id.txt", "r") as f:
                project_id = f.read()
        except:
            raise Exception(
                "No PROJECT_ID found in environment and no project_id.txt file found"
            )

    with open('models.json') as json_file:
        models_dict = json.load(json_file)

    with open('model_configs.json') as json_file:
        model_configs_dict = json.load(json_file)

    with open('datasets.json') as json_file:
        datasets_dict = json.load(json_file)

    report = {
        "scenarios": {"pyciemss": defaultdict(dict), "sciml": defaultdict(dict)},
        "services": {
            "PyCIEMSS Service": {"version": get_version(PYCIEMSS_URL)},
            "SciML Service": {"version": get_version(SCIML_URL)},
        },
    }

    scenarios = {name: {} for name in os.listdir("scenarios")}
    for scenario in scenarios:
        scenario_spec = {}
        for backend in ["pyciemss", "sciml"]:
            path = f"scenarios/{scenario}/{backend}"
            if os.path.exists(path):
                scenario_spec[backend] = [
                    f
                    for f in os.listdir(f"scenarios/{scenario}/{backend}")
                    if f.endswith(".json")
                ]  # only grab json files (ignore hidden notebooks)
        for service_name, tests in scenario_spec.items():
            for test_file in tests:
                test = test_file.split(".")[0]
                file = open(f"scenarios/{scenario}/{service_name}/{test_file}", "rb")
                logging.info(f"Trying `/{test}` ({service_name}, {scenario})")
                file_json = json.load(file)

                # replace the value of model configs and datasets with the corresponding uuid generated from the Terarium server
                model_id = None
                if "model_config_id" in file_json:
                    file_id = file_json.get("model_config_id")
                    logging.info(f"replacing model_config_id:{file_id} with {model_configs_dict.get(file_id)}")
                    file_json["model_config_id"] = model_configs_dict.get(file_id)
                    model_id = models_dict.get(file_id)
                if "dataset" in file_json:
                    logging.info(f"replacing dataset id:{file_json.get('dataset').get('id')} with {datasets_dict.get(file_json.get('dataset').get('id'))}")
                    file_json["dataset"]["id"] = datasets_dict.get(file_json.get("dataset").get("id"))
                if "model_configs" in file_json:
                    for config in file_json.get("model_configs"):
                        logging.info(f"replacing model_config id:{config.get('id')} with {model_configs_dict.get(config.get('id'))}")
                        config["id"] = model_configs_dict.get(config.get("id"))

                eval_report = eval_integration(service_name, test, file_json)
                logging.info(f"logging scenario: {service_name}:{scenario}:{test} with report: {eval_report}")
                report["scenarios"][service_name][scenario][test] = eval_report

                # Start workflow creation
                try:
                    # Setting up variables for workflow creation
                    config_ids = None
                    logging.info("Trying to get model config ID here:")
                    logging.info(file_json.get("model_config_id"))

                    if file_json.get("model_configs", None):
                        logging.info("Getting config ids")
                        logging.info(file_json.get("model_configs"))
                        config_ids = [
                            config.get("id")
                            for config in file_json.get("model_configs")
                        ]
                    else:
                        config_ids = [file_json.get("model_config_id")]

                    if file_json.get("dataset", None):
                        dataset_id = file_json.get("dataset").get("id")
                    else:
                        dataset_id = None
                    simulation_type = test + "_" + service_name
                    timespan = file_json.get("timespan", None)
                    extra = file_json.get("extra", None)

                    # Create workflow
                    workflow, workflow_id, sim_id = workflow_builder(
                        project_id=project_id,
                        workflow_name=f"{scenario}_{simulation_type}_integration_workflow",
                        workflow_description=f"Workflow for simulation integration {simulation_type}",
                        simulation_type=simulation_type,
                        model_id=model_id,
                        dataset_id=dataset_id,
                        config_ids=config_ids,
                        timespan=timespan,
                        extra=extra,
                    )

                    # put updated workflow to hmi-server
                    update_workflow(workflow_id, workflow_payload=workflow)
                    logging.info(f"Workflow updated: {workflow}")

                except Exception as e:
                    logging.error(f"Workflow creation failed: {e}")

                logging.info(f"Completed `/{test}` ({service_name}, {scenario})")
    return report


def publish_report(report, upload):
    logging.info("Publishing report")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.json"
    fullpath = os.path.join("/outputs/ta3", filename)
    os.makedirs("/outputs/ta3", exist_ok=True)
    with open(fullpath, "w") as file:
        json.dump(report, file, indent=2)

    if upload and BUCKET is not None:
        logging.info(f"Uploading report to '{BUCKET}'")
        s3 = boto3.client("s3")
        full_handle = os.path.join("ta3", filename)
        s3.upload_file(fullpath, BUCKET, full_handle)

    elif upload and BUCKET is None:
        logging.error("NO BUCKET WAS PROVIDED. CANNOT UPLOAD")

    if not upload or BUCKET is None:
        logging.info(f"{fullpath}:")
        logging.info(open(fullpath, "r").read())


def report(upload=True):
    publish_report(gen_report(), upload)


if __name__ == "__main__":
    report(UPLOAD)
