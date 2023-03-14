import os

ENV = os.environ.get("ENV", "dev")
DEPLOYMENT_FILE_PATH = os.environ.get("DEPLOYMENT_FILE_PATH", "../k8s/deployment.yml")
LOADBALANCER_FILE_PATH = os.environ.get("LOADBALANCER_FILE_PATH", "../k8s/loadbalancer.yml")
POD_LABEL = os.environ.get("POD_LABEL", "minecraft-server")
LOADBALANCER_NAME = os.environ.get("LOADBALANCER_NAME", "minecraft-lb")
SERVICE_NAMESPACE = os.environ.get("SERVICE_NAMESPACE", "default")
DEPLOYMENT_NAMESPACE = os.environ.get("DEPLOYMENT_NAMESPACE", "default")
