# minecraft-server

Minecraft server infra.

## Mincraft Server Image

This image based on gcr.io/distroless/java17-debian11. Minecraft server JAR file from SpigotMC. You can change settings by override server.properties.

### References

- [SpigotMC - High Performance Minecraft](https://www.spigotmc.org/)

- [GoogleContainerTools/distroless: 🥑 Language focused docker images, minus the operating system.](https://github.com/GoogleContainerTools/distroless)

## Architecture

![architecture](./docs/architecture.drawio.svg)

The infrastructure uses on GCP kubernetes engine. Theses actors are Deployment, Service(load balance) and PersistentVolume. The minecraft server is running on kubernetes pod. The PersistentVolume is used to store minecraft world data. The Deployment and the Service are managed by Cloud Run jobs. The Cloud Run jobs image is [python-gcloud-k8s-client-job](deploy-job/python-gcloud-k8s-client-job.Dockerfile). This image pulls kubernetes settings from GitHub repository and apply to kubernetes. The Cloud Run jobs are executed in GCP console.

## License

MIT License

## Author

[toms74209200](<https://github.com/toms74209200>)
