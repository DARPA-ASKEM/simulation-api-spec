import uuid
import os
import logging

from auth import auth_session
from utils import add_asset


TDS_URL = os.environ.get("TDS_URL", "http://hmi-server:3000")


def generate_workflow(workflow_name, workflow_description):

    workflow_payload = {
        "name": workflow_name,
        "description": workflow_description,
        "transform": {"x": 0, "y": 0, "k": 1},
        "nodes": [],
        "edges": [],
    }

    resp = auth_session().post(f"{TDS_URL}/workflows", json=workflow_payload)
    workflow_id = resp.json()["id"]

    return workflow_payload, workflow_id


def generate_model_module(model_id, workflow_id, model_config_id=None, model_num=0):
    model_module_uuid = str(uuid.uuid4())
    config_output_uuid = str(uuid.uuid4())
    default_config_output_uuid = str(uuid.uuid4())

    model_label = model_config_id
    if model_label:
        model_label = model_label.capitalize()

    model_payload = {
        "id": model_module_uuid,
        "workflowId": workflow_id,
        "operationType": "ModelOperation",
        "displayName": "Model",
        "x": 400 - (model_num * 300),
        "y": 150,
        "state": {"modelId": model_id, "modelConfigurationIds": [model_config_id]},
        "inputs": [],
        "outputs": [
            {
                "id": default_config_output_uuid,
                "type": "modelConfigId",
                "label": "Default config",
                "value": ["18d01d84-120e-452e-9ef5-1cee4c18bac1"],
                "status": "not connected",
            },
            {
                "id": config_output_uuid,
                "type": "modelConfigId",
                "label": model_label,
                "value": [model_config_id],
                "status": "connected",
            },
        ],
        "statusCode": "invalid",
        "width": 180,
        "height": 220,
    }

    return (
        model_payload,
        model_module_uuid,
        config_output_uuid,
        default_config_output_uuid,
    )


def generate_dataset_module(dataset_id, workflow_id):
    module_uuid = str(uuid.uuid4())
    dataset_output_uuid = str(uuid.uuid4())

    dataset_module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "Dataset",
        "displayName": "Dataset",
        "x": 375,
        "y": 550,
        "state": {"datasetId": dataset_id},
        "inputs": [],
        "outputs": [
            {
                "id": dataset_output_uuid,
                "type": "datasetId",
                "label": "traditional",
                "value": [dataset_id],
                "status": "connected",
            }
        ],
        "statusCode": "invalid",
        "width": 180,
        "height": 220,
    }

    return (
        dataset_module_payload,
        module_uuid,
        dataset_output_uuid
    )


def generate_calibrate_simulate_ciemms_module(
    project_id, workflow_id, config_id, dataset_id, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    dataset_uuid = str(uuid.uuid4())
    sim_output_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "CalibrationOperationCiemss",
        "type": "CALIBRATION",
        "engine": "CIEMSS",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "CalibrationOperationCiemss",
        "displayName": "Calibrate & Simulate (probabilistic)",
        "x": 1100,
        "y": 200,
        "state": {
            "chartConfigs": [
                {"selectedRun": sim_id, "selectedVariable": []}
            ],
            "mapping": [{"modelVariable": "", "datasetVariable": ""}],
            "simulationsInProgress": [],
            "timeSpan": timespan,
            "extra": extra,
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": config_id,
                "status": "connected",
                "value": [config_id],
            },
            {
                "id": dataset_uuid,
                "type": "datasetId",
                "label": dataset_id,
                "status": "connected",
                "value": [dataset_id],
            },
        ],
        "outputs": [
            {
                "id": sim_output_uuid,
                "type": "number",
                "label": "Output 1",
                "value": [{"runId": sim_id}],
                "status": "not connected",
            }
        ],
        "statusCode": "invalid",
        "width": 420,
        "height": 220,
    }

    return (
        module_payload,
        sim_id,
        module_uuid,
        config_uuid,
        dataset_uuid
    )


def generate_simulate_ciemms_module(
    project_id, workflow_id, config_id, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    sim_output_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "SimulateCiemssOperation",
        "type": "SIMULATION",
        "engine": "CIEMSS",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "SimulateCiemssOperation",
        "displayName": "Simulate (probabilistic)",
        "x": 1100,
        "y": 200,
        "state": {
            "simConfigs": {
                "runConfigs": {
                    sim_id: {
                        "runId": sim_id,
                        "active": True,
                        "configName": "Model configuration",
                        "timeSpan": timespan,
                        "numSamples": 100,
                        "method": "dopri5",
                    }
                },
                "chartConfigs": [],
            },
            "currentTimespan": timespan,
            "extra": extra,
            "numSamples": 100,
            "method": "dopri5",
            "simulationsInProgress": [],
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": "Model configuration",
                "status": "connected",
                "value": [config_id],
                "acceptMultiple": False,
            }
        ],
        "outputs": [
            {
                "id": sim_output_uuid,
                "type": "simOutput",
                "label": "Output 1",
                "value": [sim_id],
                "status": "not connected",
            }
        ],
        "status": "invalid",
        "width": 420,
        "height": 220,
    }

    return (
        module_payload,
        sim_id,
        module_uuid,
        config_uuid
    )


def generate_calibrate_ensemble_ciemss_module(
    project_id, workflow_id, config_ids, dataset_id, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    dataset_uuid = str(uuid.uuid4())
    sim_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "CalibrateEnsembleCiemms",
        "type": "ENSEMBLE",
        "engine": "CIEMSS",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "CalibrateEnsembleCiemms",
        "displayName": "Calibrate ensemble (probabilistic)",
        "x": 1100,
        "y": 200,
        "state": {
            "chartConfigs": [
                {"selectedRun": sim_id, "selectedVariable": []}
            ],
            "mapping": [{"modelVariable": "", "datasetVariable": ""}],
            "simulationsInProgress": [],
            "timeSpan": timespan,
            "extra": extra,
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": "Model configuration",
                "status": "connected",
                "value": config_ids,
                "acceptMultiple": True,
            },
            {
                "id": dataset_uuid,
                "type": "datasetId",
                "label": dataset_id,
                "status": "connected",
                "value": [dataset_id],
            },
        ],
        "outputs": [
            {
                "id": sim_uuid,
                "type": "number",
                "label": "Output 1",
                "value": [{"runId": sim_id}],
                "status": "not connected",
            }
        ],
        "statusCode": "invalid",
        "width": 420,
        "height": 220,
    }

    return module_payload, sim_id


def generate_simulate_ensemble_ciemms_module(
    project_id, workflow_id, config_ids, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    sim_output_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "SimulateEnsembleCiemms",
        "type": "ENSEMBLE",
        "engine": "CIEMSS",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "SimulateEnsembleCiemms",
        "displayName": "Simulate ensemble (probabilistic)",
        "x": 1100,
        "y": 200,
        "state": {
            "chartConfigs": [
                {"selectedRun": sim_id, "selectedVariable": []}
            ],
            "mapping": [{"modelVariable": "", "datasetVariable": ""}],
            "simulationsInProgress": [],
            "timeSpan": timespan,
            "extra": extra,
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": "Model configuration",
                "status": "connected",
                "value": config_ids,
                "acceptMultiple": True,
            }
        ],
        "outputs": [
            {
                "id": sim_output_uuid,
                "type": "number",
                "label": "Output 1",
                "value": [{"runId": sim_id}],
                "status": "not connected",
            }
        ],
        "statusCode": "invalid",
        "width": 420,
        "height": 220,
    }

    return module_payload, sim_id, module_uuid, config_uuid


# "Simulate (deterministic)"
def generate_simulate_sciml_module(
    project_id, workflow_id, model_id, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    sim_output_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "SimulateJuliaOperation",
        "type": "SIMULATION",
        "engine": "SCIML",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "SimulateJuliaOperation",
        "displayName": "Simulate (deterministic)",
        "x": 1100,
        "y": 200,
        "state": {
            "currentTimespan": timespan,
            "simConfigs": {
                "chartConfigs": [],
                "runConfigs": {
                    sim_id: {
                        "runId": sim_id,
                        "active": True,
                        "configName": "Model configuration",
                        "timeSpan": timespan,
                    }
                },
            },
            "simulationsInProgress": [],
            "extra": extra,
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": "Model configuration",
                "status": "connected",
                "value": [model_id],
                "acceptMultiple": False,
            }
        ],
        "outputs": [
            {
                "id": sim_output_uuid,
                "type": "simOutput",
                "label": "Output 1",
                "value": [sim_id],
                "status": "not connected",
            }
        ],
        "status": "invalid",
        "width": 420,
        "height": 220,
    }

    return module_payload, sim_id, module_uuid, config_uuid


# "Calibrate (deterministic)"
def generate_calibrate_sciml_module(
    project_id, workflow_id, model_id, dataset_id, timespan, extra
):
    module_uuid = str(uuid.uuid4())
    config_uuid = str(uuid.uuid4())
    dataset_uuid = str(uuid.uuid4())
    sim_output_uuid = str(uuid.uuid4())

    simulation_payload={
        "execution_payload": {},
        "name": "SimulateJuliaOperation",
        "type": "SIMULATION",
        "engine": "SCIML",
        "workflow_id": workflow_id,
        "project_id": project_id
    }
    simulation_resp = auth_session().post(
        f"{TDS_URL}/simulations",
        json=simulation_payload
    )
    if simulation_resp.status_code >= 300:
        raise Exception(
            f"Failed to create simulation ({simulation_resp.status_code} {simulation_resp.text})"
        )

    sim_id = simulation_resp.json()["id"]
    add_asset(sim_id, "SIMULATION", project_id)
    logging.info(f"simulation ID : {sim_id}")

    module_payload = {
        "id": module_uuid,
        "workflowId": workflow_id,
        "operationType": "CalibrationOperationJulia",
        "displayName": "Calibrate (deterministic)",
        "x": 1100,
        "y": 200,
        "state": {
            "chartConfigs": [],
            "calibrateConfigs": {
                "runConfigs": {
                    sim_id: {
                        "runId": sim_id,
                        "active": True,
                        "loss": [],
                    }
                },
                "chartConfigs": [[]],
            },
            "mapping": [{"modelVariable": "", "datasetVariable": ""}],
            "simulationsInProgress": [],
            "timeSpan": timespan,
            "extra": extra,
        },
        "inputs": [
            {
                "id": config_uuid,
                "type": "modelConfigId",
                "label": "Model configuration",
                "status": "connected",
                "value": [model_id],
                "acceptMultiple": False,
            },
            {
                "id": dataset_uuid,
                "type": "datasetId",
                "label": "Dataset",
                "status": "connected",
                "value": [dataset_id],
            },
        ],
        "outputs": [
            {
                "id": sim_output_uuid,
                "type": "number",
                "label": "Output 1",
                "value": [sim_id],
                "status": "not connected",
            }
        ],
        "statusCode": "invalid",
        "width": 420,
        "height": 220,
    }

    return module_payload, sim_id, module_uuid, config_uuid, dataset_uuid


def generate_edge(workflow_id, source_id, target_id, source_port, target_port):
    edge_uuid = str(uuid.uuid4())
    edge_payload = {
        "id": edge_uuid,
        "workflowId": workflow_id,
        "source": source_id,
        "sourcePortId": source_port,
        "target": target_id,
        "targetPortId": target_port,
        "points": [
            {
                "x": 0,
                "y": 0,
            },
            {
                "x": 0,
                "y": 0,
            },
        ],
    }
    return edge_payload, edge_uuid


def workflow_builder(
    project_id,
    workflow_name,
    workflow_description,
    simulation_type,
    model_id,
    dataset_id=None,
    config_ids=[],  # for ensemble
    timespan=None,
    extra=None,
):
    workflow_payload, workflow_id = generate_workflow(
        workflow_name, workflow_description
    )

    # if the length of config_ids is greater than 1, then we are building an ensemble workflow
    if len(config_ids) > 1:
        config_uuids = []
        model_num = 0
        for id in config_ids:
            (
                model_payload,
                model_module_uuid,
                config_output_uuid,
                default_config_output_uuid,
            ) = generate_model_module(id, workflow_id, id, model_num)

            workflow_payload["nodes"].append(model_payload)
            config_uuids.append(config_output_uuid)
            model_num += 1
    elif model_id:
        (
            model_payload,
            model_module_uuid,
            config_output_uuid,
            default_config_output_uuid,
        ) = generate_model_module(model_id, workflow_id, model_id)

        workflow_payload["nodes"].append(model_payload)

    if dataset_id:
        (
            dataset_payload,
            dataset_module_uuid,
            dataset_output_uuid,
        ) = generate_dataset_module(dataset_id, workflow_id)

        workflow_payload["nodes"].append(dataset_payload)

    match simulation_type:
        case "calibrate_pyciemss":
            (
                calibrate_simulate_payload,
                sim_id,
                calibrate_simulation_uuid,
                config_input_uuid,
                dataset_input_uuid,
            ) = generate_calibrate_simulate_ciemms_module(
                project_id, workflow_id, model_id, dataset_id, timespan, extra
            )
            workflow_payload["nodes"].append(calibrate_simulate_payload)

            model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                workflow_id,
                model_module_uuid,
                calibrate_simulation_uuid,
                config_output_uuid,
                config_input_uuid,
            )
            workflow_payload["edges"].append(model_simulate_edge)

            dataset_simulate_edge, dataset_simulate_edge_uuid = generate_edge(
                workflow_id,
                dataset_module_uuid,
                calibrate_simulation_uuid,
                dataset_output_uuid,
                dataset_input_uuid,
            )
            workflow_payload["edges"].append(dataset_simulate_edge)

            return workflow_payload, workflow_id, sim_id

        case "simulate_pyciemss":
            (
                simulate_ciemss_payload,
                sim_id,
                simulate_ciemss_uuid,
                config_input_uuid,
            ) = generate_simulate_ciemms_module(
                project_id, workflow_id, model_id, timespan, extra
            )
            workflow_payload["nodes"].append(simulate_ciemss_payload)

            model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                workflow_id,
                model_module_uuid,
                simulate_ciemss_uuid,
                config_output_uuid,
                config_input_uuid,
            )
            workflow_payload["edges"].append(model_simulate_edge)

            return workflow_payload, workflow_id, sim_id

        case "ensemble-calibrate_pyciemss":
            (
                calibrate_ensemble_payload,
                sim_id,
                calibrate_ensemble_uuid,
                config_input_uuid,
                dataset_input_uuid,
            ) = generate_calibrate_ensemble_ciemss_module(
                project_id,
                workflow_id,
                config_ids=config_ids,
                dataset_id=dataset_id,
                timespan=timespan,
                extra=extra,
            )
            logging.info(f"generated ensemble-calibrate_pyciemss simulation")

            workflow_payload["nodes"].append(calibrate_ensemble_payload)

            for id in config_uuids:
                model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                    workflow_id,
                    id,
                    calibrate_ensemble_uuid,
                    config_output_uuid,
                    config_input_uuid,
                )
                workflow_payload["edges"].append(model_simulate_edge)

            dataset_simulate_edge, dataset_simulate_edge_uuid = generate_edge(
                workflow_id,
                dataset_module_uuid,
                calibrate_ensemble_uuid,
                dataset_output_uuid,
                dataset_input_uuid,
            )
            workflow_payload["edges"].append(dataset_simulate_edge)

            return workflow_payload, workflow_id, sim_id

        case "ensemble-simulate_pyciemss":
            (
                simulate_ensemble_payload,
                sim_id,
                simulate_ensemble_uuid,
                config_input_uuid,
            ) = generate_simulate_ensemble_ciemms_module(
                project_id,
                workflow_id,
                config_ids=config_ids,
                timespan=timespan,
                extra=extra,
            )
            workflow_payload["nodes"].append(simulate_ensemble_payload)

            for id in config_uuids:
                model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                    workflow_id,
                    id,
                    simulate_ensemble_uuid,
                    config_output_uuid,
                    config_input_uuid,
                )
                workflow_payload["edges"].append(model_simulate_edge)

            return workflow_payload, workflow_id, sim_id

        case "simulate_sciml":
            (
                simulate_sciml_payload,
                sim_id,
                simulate_sciml_uuid,
                config_input_uuid,
            ) = generate_simulate_sciml_module(
                project_id, workflow_id, model_id, timespan, extra
            )
            workflow_payload["nodes"].append(simulate_sciml_payload)

            model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                workflow_id,
                model_module_uuid,
                simulate_sciml_uuid,
                config_output_uuid,
                config_input_uuid,
            )
            workflow_payload["edges"].append(model_simulate_edge)

            return workflow_payload, workflow_id, sim_id

        case "calibrate_sciml":
            (
                calibrate_sciml_payload,
                sim_id,
                calibrate_sciml_uuid,
                config_input_uuid,
                dataset_input_uuid,
            ) = generate_calibrate_sciml_module(
                project_id, workflow_id, model_id, dataset_id, timespan, extra
            )
            workflow_payload["nodes"].append(calibrate_sciml_payload)

            model_simulate_edge, model_simulate_edge_uuid = generate_edge(
                workflow_id,
                model_module_uuid,
                calibrate_sciml_uuid,
                config_output_uuid,
                config_input_uuid,
            )
            workflow_payload["edges"].append(model_simulate_edge)

            dataset_simulate_edge, dataset_simulate_edge_uuid = generate_edge(
                workflow_id,
                dataset_module_uuid,
                calibrate_sciml_uuid,
                dataset_output_uuid,
                dataset_input_uuid,
            )
            workflow_payload["edges"].append(dataset_simulate_edge)

            return workflow_payload, workflow_id, sim_id

    logging.info(f"Unable to find simulation type, return simple workflow: {workflow_payload}")
    return workflow_payload, workflow_id, None
