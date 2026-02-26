# Base image: ubuntu:22.04
FROM ubuntu:22.04

# ARGs
# https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# neo4j 2025.08.0 installation (match GDS v2.21.0) and some cleanup
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common && \
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y nano unzip neo4j=1:2025.08.0 python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create working dir and switch to it
RUN mkdir -p /neo4j_project
WORKDIR /neo4j_project

# Download the March 2022 NYC Yellow Taxi parquet to /neo4j_project
RUN wget -O /neo4j_project/yellow_tripdata_2022-03.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet

# Install OpenJDK 21 and set JAVA_HOME (compatible on amd64/arm64)
RUN apt-get update && apt-get install -y openjdk-21-jdk ca-certificates && \
    rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
RUN realhome="$(dirname $(dirname $(readlink -f $(which java))))" && \
    ln -sfn "$realhome" /usr/lib/jvm/java-21-openjdk-amd64

# Upgrade pip and install required Python packages
RUN python3 -m pip install --upgrade pip && \
    pip3 install neo4j pandas pyarrow

# Install Neo4j GDS plugin v2.21.0
RUN mkdir -p /var/lib/neo4j/plugins && \
    wget -O /var/lib/neo4j/plugins/neo4j-graph-data-science-2.21.0.jar \
    https://github.com/neo4j/graph-data-science/releases/download/2.21.0/neo4j-graph-data-science-2.21.0.jar

# Configure Neo4j for remote access and procedure allowlists
RUN echo "server.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf && \
    echo "server.bolt.listen_address=:7687" >> /etc/neo4j/neo4j.conf && \
    echo "server.http.listen_address=:7474" >> /etc/neo4j/neo4j.conf 

# Set default Neo4j password non-interactively
RUN neo4j-admin dbms set-initial-password graphprocessing

# Copy your loader script into /neo4j_project
COPY data_loader.py /neo4j_project/data_loader.py



# Run the data loader script
RUN chmod +x /neo4j_project/data_loader.py && \
    neo4j start && \
    python3 data_loader.py && \
    neo4j stop

# Expose neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]
