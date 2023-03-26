from logging import DEBUG, getLogger
from typing import Any

from google.cloud.logging import Client
from kubernetes import client, config


logging_client = Client()
logging_client.setup_logging()
logger = getLogger(__name__)
logger.setLevel(DEBUG)


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


if __name__ == "__main__":
    logger.info("Start creating")
    k8s = K8sClient()
    pods = k8s.get_pods()
    logger.info(pods)
