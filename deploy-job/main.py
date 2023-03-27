import glob
import os
import shutil
import sys
import tarfile
import time
from logging import DEBUG, getLogger
from typing import Any

import requests
import yaml
from google.cloud.logging import Client
from kubernetes import client, config

ENV = os.environ.get("ENV", "dev")
DEPLOYMENT_FILE_NAME = os.environ.get("DEPLOYMENT_FILE_NAME", "deployment.yml")
LOADBALANCER_FILE_NAME = os.environ.get("LOADBALANCER_FILE_NAME", "loadbalancer.yml")
DEPLOYMENT_FILE_PATH = os.environ.get("DEPLOYMENT_FILE_PATH", "../k8s") + "/" + DEPLOYMENT_FILE_NAME
LOADBALANCER_FILE_PATH = os.environ.get("LOADBALANCER_FILE_PATH", "../k8s") + "/" + LOADBALANCER_FILE_NAME
POD_LABEL = os.environ.get("POD_LABEL", "minecraft-server")
LOADBALANCER_NAME = os.environ.get("LOADBALANCER_NAME", "minecraft-lb")
SERVICE_NAMESPACE = os.environ.get("SERVICE_NAMESPACE", "default")
DEPLOYMENT_NAMESPACE = os.environ.get("DEPLOYMENT_NAMESPACE", "default")

CLUSTER_NAME = os.environ.get("CLUSTER_NAME")
REGION = os.environ.get("REGION")
PROJECT_ID = os.environ.get("PROJECT_ID")

GITHUB_REPOSITORY = os.environ.get("REPOSITORY")
PROPERTY_KEY_TARBALL = "tarball_url"
PROPERTY_KEY_NAME = "name"
DOWNLOAD_PATH = "/tmp"
GITHUB_API_URL = "https://api.github.com"
GITHUB_API_REPOSITORY_PATH = "/repos"
GITHUB_API_RELEASES_PATH = "/releases"
GITHUB_API_LATEST_PATH = "/latest"
GITHUB_API_LATEST_RELEASE_URL = f"{GITHUB_API_URL}{GITHUB_API_REPOSITORY_PATH}/{GITHUB_REPOSITORY}{GITHUB_API_RELEASES_PATH}{GITHUB_API_LATEST_PATH}"
ACCEPT_HEADER = "application/vnd.github+json"
INTERVAL_SECONDS = 10

logging_client = Client()
logging_client.setup_logging()
logger = getLogger(__name__)
logger.setLevel(DEBUG)


def get_latest_release() -> dict:
    headers = {"Accept": ACCEPT_HEADER}
    response = requests.get(GITHUB_API_LATEST_RELEASE_URL, headers=headers)
    if response.status_code != 200:
        return {}
    response_json = response.json()
    if not response_json:
        return {}
    return response_json


def get_release_archive(url: str, file_name: str) -> None:
    headers = {"Accept": ACCEPT_HEADER}
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code != 200:
        return
    file_path = file_name if ENV == "dev" else os.path.join(DOWNLOAD_PATH, file_name)
    with open(file_path, "wb") as f:
        f.write(response.raw.read())


def extract_archive(file: str) -> None:
    yaml_files = []
    file_path = file if ENV == "dev" else os.path.join(DOWNLOAD_PATH, file)
    with tarfile.open(file_path, "r:gz") as f:
        menbers = f.getnames()
        for i in menbers:
            if "yml" in i:
                yaml_files.append(i)
                f.extract(i, path=DOWNLOAD_PATH)

    for i in yaml_files:
        p = i if ENV == "dev" else os.path.join(DOWNLOAD_PATH, i)
        shutil.move(p, DOWNLOAD_PATH)


def delete_archive(file: str) -> None:
    file_path = file if ENV == "dev" else os.path.join(DOWNLOAD_PATH, file)
    os.remove(file_path)


def fetch_resources():
    result = get_latest_release()
    archive = f"{result[PROPERTY_KEY_NAME]}.tar.gz"
    get_release_archive(result[PROPERTY_KEY_TARBALL], archive)
    extract_archive(archive)
    delete_archive(archive)


def load_yaml(file: str):
    file_path = file if ENV == "dev" else os.path.join(os.path.dirname(DOWNLOAD_PATH), file)
    if not os.path.isfile(file_path):
        return
    with open(file_path) as f:
        return yaml.safe_load(f)


class K8sClient:
    def __init__(self):
        config.load_kube_config()

    def get_pods(self) -> list[Any]:
        v1 = client.CoreV1Api()
        ret = v1.list_pod_for_all_namespaces(watch=False)
        pods = []
        for i in ret.items:
            pods.append(i)
        return pods

    def get_services(self, namespace: str) -> list[Any]:
        v1 = client.CoreV1Api()
        services = v1.list_namespaced_service(namespace=namespace)
        return services.items

    def apply_deployment(self, file: str) -> None:
        resource = load_yaml(file)
        v1 = client.AppsV1Api()
        v1.create_namespaced_deployment(body=resource, namespace=DEPLOYMENT_NAMESPACE)

    def delete_deployment(self, name: str) -> None:
        v1 = client.AppsV1Api()
        v1.delete_namespaced_deployment(name=name, namespace=DEPLOYMENT_NAMESPACE)

    def apply_service(self, file: str) -> None:
        resource = load_yaml(file)
        v1 = client.CoreV1Api()
        v1.create_namespaced_service(body=resource, namespace=SERVICE_NAMESPACE)

    def delete_service(self, name: str) -> None:
        v1 = client.CoreV1Api()
        v1.delete_namespaced_service(name=name, namespace=SERVICE_NAMESPACE)


if __name__ == "__main__":
    logger.info("Start creating")
    fetch_resources()
    root_dir = "." if ENV == "dev" else DOWNLOAD_PATH
    resources = glob.glob("*.yml", root_dir=root_dir)
    logger.info(f"resources: {resources}")
    k8s = K8sClient()
    k8s.apply_deployment(DEPLOYMENT_FILE_PATH)
    k8s.apply_service(LOADBALANCER_FILE_PATH)

    created = False
    interval = INTERVAL_SECONDS
    while not created:
        pods_created = False
        pods = k8s.get_pods(POD_LABEL)
        pods_created = len(pods) > 0
        for i in pods:
            logger.debug("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        services = k8s.get_services(SERVICE_NAMESPACE)
        service_created = False
        for i in services:
            logger.debug(
                "%s\t%s\t%s\t%s"
                % (
                    i.metadata.name,
                    i.spec.cluster_ip,
                    i.spec.type,
                    i.spec.ports[0].port,
                )
            )
            service_created = i.metadata.name == LOADBALANCER_NAME
        created = pods_created and service_created
        if created:
            sys.exit()
        time.sleep(interval)
        interval = interval * 2
        if interval >= 300:
            logger.warn("Create failed.")
            sys.exit(1)
