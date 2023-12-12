FROM ghcr.io/toms74209200/python-gcloud-k8s-client:3.9-bullseye

COPY requirements.txt /requirements.txt
RUN pip install -U pip && pip install --no-cache-dir -r /requirements.txt

COPY main.py /main.py
CMD ["main.py", "create"]
