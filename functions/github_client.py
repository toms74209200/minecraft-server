import shutil
import tarfile

import requests
from env import GITHUB_REPOSITORY, PROPERTY_KEY_NAME, PROPERTY_KEY_TARBALL

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_REPOSITORY_PATH = "/repos"
GITHUB_API_RELEASES_PATH = "/releases"
GITHUB_API_LATEST_PATH = "/latest"
GITHUB_API_LATEST_RELEASE_URL = f"{GITHUB_API_URL}{GITHUB_API_REPOSITORY_PATH}/{GITHUB_REPOSITORY}{GITHUB_API_RELEASES_PATH}{GITHUB_API_LATEST_PATH}"
ACCEPT_HEADER = "application/vnd.github+json"


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
    with open(file_name, "wb") as f:
        f.write(response.raw.read())


def extract_archive(file: str) -> None:
    yaml_files = []
    with tarfile.open(file, "r:gz") as f:
        menbers = f.getnames()
        for i in menbers:
            if "yml" in i:
                yaml_files.append(i)
                f.extract(i)

    for i in yaml_files:
        shutil.move(i, ".")


if __name__ == "__main__":
    result = get_latest_release()
    archive = f"{result[PROPERTY_KEY_NAME]}.tar.gz"
    get_release_archive(result[PROPERTY_KEY_TARBALL], archive)
    extract_archive(archive)
