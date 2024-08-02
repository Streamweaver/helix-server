# Helix Server

[![Build Status](https://github.com/idmc-labs/helix-server/actions/workflows/test_runner.yml/badge.svg)](https://github.com/idmc-labs/helix-server/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/2322f4f0041caffe4742/maintainability)](https://codeclimate.com/github/idmc-labs/helix-server/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/2322f4f0041caffe4742/test_coverage)](https://codeclimate.com/github/idmc-labs/helix-server/test_coverage)

## Initialize environment

Create a `.env` file in the project folder. (For development, blank file is fine)

## Get started with:

```bash
docker-compose up
```

## Initialize database

```bash
./init.sh
```

## Initialize database (seed)
```bash
# Fix the full_name constraint
docker-compose exec server python manage.py save_users_dummy
docker-compose exec server python manage.py create_dummy_users

docker-compose exec server python manage.py loadtestdata <case sensitive model_names> --count 2
# eg.
# docker-compose exec server python manage.py loadtestdata Country --count 2
# docker-compose exec server python manage.py loadtestdata Resource ResourceGroup --count 2
```

And navigate to `localhost:9000/graphiql` to view available graphs.
Use `localhost:9000/graphql` to interact with the server from the client.

## One time commands

### Save geojson for each country

```bash
python manage.py split_geojson
```

### Generate fresh graphql schema.
```bash
python manage.py graphql_schema --out schema.graphql
```

## Populate pre 2016 conflict and disaster data for GIDD
```bash
python manage.py update_pre_2016_gidd_data.py old_conflict_data.csv old_disaster_data.csv
```
### Populate IDPs SADD estimates table
```bash
python manage.py update_idps_sadd_estimates idps_sadd_estimates.csv
```

### Setup S3 buckets

This will create appropriate buckets with required policies based on the `.env`.

```bash
sh deploy/scripts/s3_bucket_setup.sh
```

### To enable two factor authentication (generate statictoken) of admin user from command line
```bash
python manage.py addstatictoken -t 123456 "admin@idmcdb.org"
```

## Management Command
There are custom management commands available to facilitate specific tasks.

### Populate figure `Calculation Logic`
```bash
./manage.py populate_calculation_logic_field
```
> NOTE: This command populates the `calculation_logic` field in the Figure Table if there is no existing data in it.

### Populate Household Size table and update AHHS data for the year 2024
```bash
./manage.py update_ahhs_2024 update_ahhs.csv
```
> NOTE: This command populates the HouseholdSize Table and updates AHHS data in the Figure Table specifically for the year 2024.

### Force Update GIDD Data
```bash
./manage.py force_update_gidd_data
```
> NOTE: This command forces an update of GIDD data. It's important to note that this command is intended for local development purposes only, so it should be used with caution.


## Deployment Instructions for Helix Django Application

This document provides step-by-step instructions for deploying the Helix Django application to a production environment.    

### Prerequisites

Before proceeding with the deployment, ensure that you have the following prerequisites in place:

- Docker and Docker Compose installed (if deploying with Docker)
- AWS account and necessary permissions (if deploying to AWS)
- PostgreSQL database instance or cluster
- Redis instance or cluster
- Amazon S3 buckets for static files and media storage

### 1. Set up the Web Server

The Helix application is designed to be deployed with uWSGI as the web server.

1. Install and configure uWSGI on your server.
2. Use the provided `deploy/scripts/run_prod.sh` script to start the uWSGI server with the configuration specified in `deploy/configs/uwsgi.ini`.

```bash
./deploy/scripts/run_prod.sh
```

### 2. Set up the Database

1. Provision a PostgreSQL database instance or cluster.
2. Configure the database connection settings in the `helix/settings.py` file with the appropriate credentials and connection details.
3. Run Django migrations to set up the database schema.

```bash
python manage.py migrate
```

### 3. Set up Redis Cache

1. Provision a Redis instance or cluster for caching purposes.
2. Configure the Redis settings in the `helix/caches.py` file with the appropriate connection details.

### 4. Set up Static Files and Media Storage

1. Create the required S3 buckets for storing static files and media files using the `deploy/scripts/s3_bucket_setup.sh` script.

```bash
./deploy/scripts/s3_bucket_setup.sh
```

2. Configure the storage settings in the `helix/storages.py` file with the appropriate S3 bucket names and AWS credentials. 

### 5. Set up Background Tasks

1. Configure Celery settings in the `helix/celery.py` file.
2. Use the `deploy/scripts/run_tasks.sh` script to start the Celery worker process.

```bash
./deploy/scripts/run_tasks.sh
```

### 6. Set Environment Variables

Set the required environment variables for the application, such as database credentials, AWS credentials, and other sensitive information.

### 7. Docker Deployment

If deploying with Docker, follow these steps:

1. Build Docker images for the API and worker components using the provided Dockerfiles (`api.Dockerfile` and `worker.Dockerfile`).
2. Use the `docker-compose.yml` file to run the application in Docker containers, ensuring that the required services (database, Redis, etc.) are also set up and linked appropriately.

```bash
docker-compose up -d
```

### 8. AWS Deployment

If deploying to AWS, follow these steps:

1. Use the AWS Copilot manifests and addons in the `copilot` directory to deploy the application to AWS services like ECS (Elastic Container Service).
2. Set up the required resources, such as the database cluster, S3 buckets, Redis cache, and other necessary components, using the provided configurations.

### 9. Set up CI/CD Pipeline

1. Configure a CI/CD pipeline using the GitHub Actions workflows in the `.github/workflows` directory for linting and running tests.
2. Set up a CI/CD pipeline for AWS deployment using the buildspec and manifest in the `copilot/pipelines/helix-pipeline` directory.

### 10. Initialize Data

Run Django management commands and load fixtures to initialize data, such as countries, organizations, and user roles.      

```bash
python manage.py loaddata fixtures/countries.json
python manage.py loaddata fixtures/organizations.json
python manage.py loaddata fixtures/user_roles.json
```

### 11. Set up Logging and Monitoring

Configure Sentry for error logging and monitoring using the settings in the `helix/sentry.py` file.

### 12. Review Documentation

Refer to the deployment-related documentation, such as the `Deployment.md` file, for any additional details or instructions specific to the application deployment.

Please note that the specific steps and configurations may vary depending on the deployment environment and infrastructure setup. It's recommended to review the documentation thoroughly and adjust the instructions as needed.