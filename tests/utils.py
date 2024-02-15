from datetime import datetime
import os
import requests
import logging

from auth import auth_session


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TDS_URL = os.environ.get("TDS_URL", "http://hmi-server:3000")


def create_project():
    """
    Generate test project in TDS
    """
    current_timestamp = datetime.now()
    ts = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    project = {
        "name": "Integration Test Suite Project",
        "description": f"Test generated at {ts}",
        "assets": [],
        "active": True,
    }

    resp = auth_session().post(f"{TDS_URL}/projects", json=project)
    project_id = resp.json()["id"]

    return project_id


def add_asset(resource_id, resource_type, project_id):
    if not project_id:
        try:
            with open("project_id.txt", "r") as f:
                project_id = f.read()
        except:
            raise Exception(
                "No PROJECT_ID found in environment and no project_id.txt file found"
            )
    logging.info(
        f"Adding asset {resource_id} of type {resource_type} to project {project_id}"
    )
    resp = auth_session().post(
        f"{TDS_URL}/projects/{project_id}/assets/{resource_type}/{resource_id}"
    )
    if resp.status_code == 409:
        logging.info(
            f"Asset {resource_id} of type {resource_type} already exists in project {project_id}"
        )
        logging.info(
            "Asset should have been updated in TDS by POST requests, no need to add it to the project again."
        )
        return resp.json()
    elif resp.status_code >= 300:
        logging.error(
            f"Failed to add asset to project: status - {resp.status_code}: {resp.json()}"
        )
        return resp.json()

    provenance_payload = {
        "relation_type": "CONTAINS",
        "left": project_id,
        "left_type": "Project",
        "right": resource_id,
        "right_type": resource_type[
            :-1
        ].capitalize(),  # Converts "models" to "Model", etc.
    }
    prov_resp = auth_session().post(f"{TDS_URL}/provenance", json=provenance_payload)

    if prov_resp.status_code >= 300:
        logging.error(
            f"Failed to add provenance for project CONTAINS {resource_type}: status - {prov_resp.status_code}: {prov_resp.json()}"
        )
    return resp.json()
