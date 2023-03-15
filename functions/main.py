import glob
from logging import DEBUG, getLogger
import time
from enum import Enum, auto

import flask
import functions_framework
from env import (
    DEPLOYMENT_FILE_PATH,
    LOADBALANCER_FILE_PATH,
    LOADBALANCER_NAME,
    POD_LABEL,
    PROPERTY_KEY_NAME,
    PROPERTY_KEY_TARBALL,
    SERVICE_NAMESPACE,
)
from flask import make_response
from github_client import extract_archive, get_latest_release, get_release_archive
from k8s_client import apply_deployment, apply_service, delete_deployment, delete_service, get_pods, get_services
from verify import verify

logger = getLogger(__name__)
logger.setLevel(DEBUG)

PROPERTY_ORDER = "order"
INTERVAL_SECONDS = 10


class OrderType(Enum):
    CREATE = auto()
    DELETE = auto()


def get_order_type(value: str) -> OrderType:
    if value == "create":
        return OrderType.CREATE
    if value == "delete":
        return OrderType.DELETE
    return OrderType.DELETE


def fetch_resources():
    result = get_latest_release()
    archive = f"{result[PROPERTY_KEY_NAME]}.tar.gz"
    get_release_archive(result[PROPERTY_KEY_TARBALL], archive)
    extract_archive(archive)


def create() -> bool:
    logger.info("create")
    fetch_resources()
    resources = glob.glob("*.yml")
    logger.info(f"resources: {resources}")
    apply_deployment(DEPLOYMENT_FILE_PATH)
    apply_service(LOADBALANCER_FILE_PATH)

    created = False
    interval = INTERVAL_SECONDS
    while not created:
        pods_created = False
        pods = get_pods(POD_LABEL)
        pods_created = len(pods) > 0
        for i in pods:
            logger.debug("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        services = get_services(SERVICE_NAMESPACE)
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
            return True
        time.sleep(interval)
        interval = interval * 2
        if interval >= 300:
            logger.warn("Create failed.")
            return False


def delete() -> bool:
    logger.info("delete")
    delete_deployment(POD_LABEL)
    delete_service(LOADBALANCER_NAME)
    deleted = False
    interval = INTERVAL_SECONDS
    while not deleted:
        pods = get_pods(POD_LABEL)
        pods_deleted = not pods
        services = get_services(SERVICE_NAMESPACE)
        service_deleted = False
        for i in services:
            service_deleted = i.metadata.name != LOADBALANCER_NAME
        deleted = pods_deleted and service_deleted
        if delete:
            return True
        time.sleep(interval)
        interval = interval * 2
        if interval >= 300:
            logger.warn("Delete faild.")
            return False


# Register an HTTP function with the Functions Framework
@functions_framework.http
def manage(request: flask.Request):
    logger.info(f"request: {request}")
    if request.method != "POST":
        return make_response("Method Not Allowed", 405)

    authorization = request.authorization
    if not authorization:
        return make_response("Unauthorized", 401)

    if not verify(authorization):
        return make_response("Unauthorized", 401)

    if not request.is_json:
        return make_response("Bad Request", 400)

    request_json = request.get_json()
    order = get_order_type(request_json[PROPERTY_ORDER])
    success = False
    if order == OrderType.CREATE:
        success = create()
    elif order == OrderType.DELETE:
        success = delete()

    if success:
        return "OK"
    else:
        return make_response("Internal Server Error", 500)


if __name__ == "__main__":
    create()
    delete()
