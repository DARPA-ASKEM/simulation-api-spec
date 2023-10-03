# Testrunner for TA3
`simulation-integration` generates an integration report by
standing up all of the relevant TA3 services with a Docker Compose
and trying to use a few requests through the relevant parts of the stack.

## Usage
Run `docker compose up`. Once the `tests` container completes, the report is done.

See `env.sample` to see what to populate `.env` with.

## Adding Scenarios
To add scenarios, create a new directory in `scenarios`. For each request you would like to 
try out, create a file `scenarios/{scenario_name}/{backend-service}/{endpoint-name}.json`. For example, a PyCIEMSS
`simulate` scenario can be added by putting the payload in `scenarios/{scenario_name}pyciemss/simulate.json`.

These requests will need to reference assets in TDS which are prepopulated by `tests/seed.py`. To add more resources,
go to `data/datasets` to add a CSV and `data/model` to add a configuration.