import os
import json
from time import sleep, time

import boto3
import requests

TDS_URL = os.environ.get("TDS_URL", "http://data-service:8000")
PYCIEMSS_URL = os.environ.get("PYCIEMSS_URL", "http://pyciemss-api")
SCIML_URL = os.environ.get("SCIML_URL", "http://sciml-service")
BUCKET = os.environ.get("BUCKET", None)


def eval_integration(service_name, endpoint, request):
    start_time = time()
    is_success = False
    base_url = PYCIEMSS_URL if service_name == "pyciemss" else SCIML_URL
    kickoff_request = requests.post(f"{base_url}/{endpoint}", data=request)
    if kickoff_request.status_code < 300:
        sim_id = kickoff_request.json()["simulation_id"]
        get_status = lambda: request.get(f"{base_url}/{endpoint}/status/{sim_id}").json()["status"]
        while get_status() in ["queued", "running"]:
            sleep(1)
        if get_status() == "complete":
            is_success = True
    return {
        "Integration Status": is_success,
        "Execution Time": time() - start_time
    }


def gen_report():
    report = {
        "scenarios": {
            "PyCIEMSS": {},
            "SciML": {}
        }, 
        "services": {
            "TDS": {
                "version": "UNAVAILABLE"
            },
            "PyCIEMSS Service": {
                "version": "UNAVAILABLE"
            },
            "SciML Service": {
                "version": "UNAVAILABLE"
            },
        }
    }

    
    report["scenarios"] = {name: {} for name in os.listdir("scenarios")}
    for scenario in report["scenarios"]:
        scenario_spec = {
            "pyciemss": os.listdir(f"scenarios/{scenario}/pyciemss"),
            "sciml": os.listdir(f"scenarios/{scenario}/sciml")
        }
        for service_name, tests in scenario_spec.items():
            for test_file in tests:
                test = test_file.strip(".json")
                name = f"{service_name}-{test}"
                report["scenarios"][scenario][name] = eval_integration(service_name, test, json.load(f"scenarios/{scenario}/{test_file}"))
    return report


def publish_report(report, upload):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"report_{timestamp}.json"
    fullpath = os.path.join("reports", filename)
    with open(fullpath, "w") as file:
        json.dump(report, file, indent=2)

    if upload:
        s3 = boto3.client("s3")
        full_handle = os.path.join("ta3", filename)
        s3.upload_file(fullpath, BUCKET, full_handle)


def report(upload=True):
    publish_report(gen_report())


if __name__ == "__main__":
    report(BUCKET is not None)
