FROM ghcr.io/toms74209200/python-gcloud-k8s-client:0.0.2

COPY main.py /main.py
CMD ["main.py"]
