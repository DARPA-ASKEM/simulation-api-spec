import os
import json
from time import sleep, time

import boto3
import requests

TDS_URL = os.environ("TDS_URL", "data-service")
PYCIEMSS_URL = os.environ("PYCIEMSS_URL", "pyciemss-api")
SCIML_URL = os.environ("SCIML_URL", "sciml-service")
BUCKET = os.environ("BUCKET", "jataware-sim-service-test")


def eval_integration(service_name, endpoint, request):
    start_time = time()
    is_success = False
    base_url = PYCIEMSS_URL if service_name == "pyciemss" else SCIML_URL
    kickoff_request = requests.post(f"{base_url}/{endpoint}", data=request)
    if kickoff_request.status_code < 300:
        sim_id = kickoff_request.json()["simulation_id"]
        get_status = lambda: request.get(f"{base_url}/{endpoint}/status/{sim_id}").json()["status"]
        while (status := get_status()) in ["queued", "running"]:
            sleep(5)
            status = get_status()
        if status == "complete"
            is_success = True


    return {
        "Integration Status": is_success,
        "Execution Time": time() - start_time
    }


def gen_report():
    report = {"scenarios": {}, "services": {}}
    report["scenarios"] = {name: {} for name in os.listdir("scenarios")}
    for scenario in scenarios:
        scenario_spec = {
            "pyciemss": os.listdir(f"scenario/{scenario}/pyciemss"),
            "sciml": os.listdir(f"scenario/{scenario}/sciml")
        }
        for service_name, tests in scenario_spec:
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
    report()
