# process-mining-for-bots

This framework provides modules that can be used to do various process mining tasks on bot models. It also contains a demo notebook that demonstrates how to use the framework.

## Installation

1. Clone this repository
2. (Optional) Create a virtual environment using `python -m venv venv`
3. Install the requirements using `pip install -r requirements.txt`

## Usage

The usage of this framework is demonstrated in the `demo.ipynb` notebook. You can run the notebook to see how to use the framework.

## Assets

The `assets` folder contains some sample data that can be used to test the framework. The `assets` folder contains event logs and bot models in the `event_logs` and `models` folders respectively.

## REST API

This repository also contains a Flask app REST API that can be used to interact with the framework and a Dockerfile to run the app in a container. To run the app, follow these steps:

- configure the environment variables in the `.env` file, you can use the `.env.example` file as a template. In most cases, you will not need to change the values.
- Build the Docker image using `docker build -t process-mining-for-bots .`
- Run docker compose using `docker compose up`
