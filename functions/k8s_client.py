import os
import sys
import time
from typing import Any

import yaml
from env import (
    DEPLOYMENT_FILE_PATH,
    DEPLOYMENT_NAMESPACE,
    ENV,
    LOADBALANCER_FILE_PATH,
    LOADBALANCER_NAME,
    POD_LABEL,
    SERVICE_NAMESPACE,
)
from kubernetes import client, config


def load_yaml(file: str):
    file_path = file if ENV == "local" else os.path.join(os.path.dirname(__file__), file)
    if not os.path.isfile(file_path):
        return
    with open(file_path) as f:
        return yaml.safe_load(f)


class K8sClient:
    def __init__():
        config.load_kube_config()

    def get_pods(label: str) -> list[Any]:
        v1 = client.CoreV1Api()
        ret = v1.list_pod_for_all_namespaces(watch=False)
        pods = []
        for i in ret.items:
            if label in i.metadata.name:
                pods.append(i)
        return pods

    def get_services(namespace: str) -> list[Any]:
        v1 = client.CoreV1Api()
        services = v1.list_namespaced_service(namespace=namespace)
        return services.items

    def apply_deployment(file: str) -> None:
        resource = load_yaml(file)
        v1 = client.AppsV1Api()
        v1.create_namespaced_deployment(body=resource, namespace=DEPLOYMENT_NAMESPACE)

    def delete_deployment(name: str) -> None:
        v1 = client.AppsV1Api()
        v1.delete_namespaced_deployment(name=name, namespace=DEPLOYMENT_NAMESPACE)

    def apply_service(file: str) -> None:
        resource = load_yaml(file)
        v1 = client.CoreV1Api()
        v1.create_namespaced_service(body=resource, namespace=SERVICE_NAMESPACE)

    def delete_service(name: str) -> None:
        v1 = client.CoreV1Api()
        v1.delete_namespaced_service(name=name, namespace=SERVICE_NAMESPACE)


if __name__ == "__main__":
    interval = 10
    k8s = K8sClient()

    k8s.apply_deployment(DEPLOYMENT_FILE_PATH)
    k8s.apply_service(LOADBALANCER_FILE_PATH)

    print("Creating.")
    created = False
    while not created:
        pods_created = False
        pods = k8s.get_pods(POD_LABEL)
        pods_created = len(pods) > 0
        for i in pods:
            print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        services = k8s.get_services(SERVICE_NAMESPACE)
        service_created = False
        for i in services:
            print(
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
        time.sleep(interval)
        interval = interval * 2
        if interval >= 300:
            print("Create failed.")
            sys.exit(1)

    print("Create success!")

    interval = 10

    k8s.delete_deployment(POD_LABEL)
    k8s.delete_service(LOADBALANCER_NAME)

    print("Deleting.")
    deleted = False
    while not deleted:
        pods = k8s.get_pods(POD_LABEL)
        pods_deleted = not pods
        services = k8s.get_services(SERVICE_NAMESPACE)
        service_deleted = False
        for i in services:
            service_deleted = i.metadata.name != LOADBALANCER_NAME
        deleted = pods_deleted and service_deleted
        time.sleep(interval)
        interval = interval * 2
        if interval >= 300:
            print("Delete faild.")
            sys.exit(1)

    print("Delete success!")
