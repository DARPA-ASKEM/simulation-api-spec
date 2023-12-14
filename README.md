# Testrunner for TA3
`simulation-integration` generates an integration report by
standing up all of the relevant TA3 services with a Docker Compose
and trying to use a few requests through the relevant parts of the stack.

## Usage

### Step by Step Guide

1. Create a [GitHub Personal Access Token (classic)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) that grants scope access to
   - [x] .`workflow`,
   - [x] `read:packages`,
   - [x] `write:packages`
   - [x] and `delete:packages`.
1. Execute `echo [YOUR_GITHUB_TOKEN] | docker login ghcr.io -u [YOUR_GITHUB_USERNAME] --password-stdin`  in the `simulation-integration` directory
1. Update your containers by running `docker compose pull`
1. Create `.env` by running `cp env.sample .env` 
1. Build your containers by `docker compose build`
1. Run the tests with `docker compose run tests`.
1. View the results with `docker compose run --build --service-ports dashboard` (Assuming you haven't deleted any volumes)


### Usage Details
   
Once the `tests` container completes, the report is done.

If run with UPLOAD=TRUE as an environment variable, the report will be uploaded to S3.
Otherwise, the report is output as part of the `tests` container's logs.

The logs can be viewed by running `docker compose logs -f tests`.

Note: The services used in testing are not cleaned up following testing. When done with running tests,
be sure to shut down the services by running `docker compose down` to conserve your resources.

See `env.sample` to see which environment variables are used by the test/report runner. 
You can create a `.env` envfile based on sample if you want to override the defaults.

## Adding Scenarios
To add scenarios, create a new directory in `scenarios`. For each request you would like to 
try out, create a file `scenarios/{scenario_name}/{backend-service}/{endpoint-name}.json`. For example, a PyCIEMSS
`simulate` scenario can be added by putting the payload in `scenarios/{scenario_name}pyciemss/simulate.json`.

These requests will need to reference assets in TDS which are prepopulated by `tests/seed.py`. To add more resources,
go to `data/datasets` to add a CSV and `data/model` to add a configuration.
