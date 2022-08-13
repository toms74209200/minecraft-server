ARG SPIGOT_VERSION=1.19.2

FROM openjdk:17.0.2-slim-bullseye AS build-spigotmc

ARG SPIGOT_VERSION

WORKDIR /usr/local/bin
RUN apt-get update && apt-get install -y \
    wget \
    git
RUN wget https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar \
    && java -jar BuildTools.jar --rev ${SPIGOT_VERSION} \
    && mv spigot-${SPIGOT_VERSION}.jar server.jar
RUN echo eula=true > eula.txt

FROM gcr.io/distroless/java17-debian11

COPY --from=build-spigotmc /usr/local/bin/server.jar /usr/local/bin/server.jar
COPY --from=build-spigotmc /usr/local/bin/eula.txt /usr/local/bin/eula.txt
WORKDIR /usr/local/bin
CMD ["-Xmx2048M", "-Xms1024M", "-jar", "/usr/local/bin/server.jar", "nogui"]