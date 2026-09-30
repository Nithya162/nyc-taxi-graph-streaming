# Base image: ubuntu:22.04
FROM ubuntu:22.04

# Arguments for platform and non-interactive 
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

RUN mkdir -p /cse511
WORKDIR /cse511

RUN wget -O yellow_tripdata_2022-03.parquet \
    https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet && \
    ls -lh yellow_tripdata_2022-03.parquet

COPY ./data_loader.py /cse511/data_loader.py

# Install Java (OpenJDK 21)
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Upgrade pip and install required Python packages
RUN pip3 install --upgrade pip && \
    pip3 install neo4j pandas pyarrow

RUN wget -O /var/lib/neo4j/plugins/neo4j-graph-data-science-2.21.0.jar \
    https://github.com/neo4j/graph-data-science/releases/download/2.21.0/neo4j-graph-data-science-2.21.0.jar && \
    ls -lh /var/lib/neo4j/plugins/


RUN echo "server.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf && \
    echo "dbms.security.procedures.unrestricted=apoc.*,gds.*" >> /etc/neo4j/neo4j.conf && \
    echo "dbms.security.procedures.allowlist=apoc.*,gds.*" >> /etc/neo4j/neo4j.conf
RUN neo4j-admin dbms set-initial-password graphprocessing
# Download the dataset
# Install curl
#RUN apt-get update && apt-get install -y curl

# Create the directory
#RUN mkdir -p /CSE511

# Install curl (if not installed)
#RUN apt-get update && apt-get install -y curl

# Download the dataset
#RUN curl -o /CSE511/yellow_tripdata_2022-03.parquet https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet


# Set up environment variables and Neo4j configuration
#ENV NEO4J_AUTH=neo4j/project1phase1
# Download and move the GDS plugin to the plugins directory
#RUN wget -O /var/lib/neo4j/plugins/neo4j-graph-data-science-2.3.1.jar \
    #https://graphdatascience.ninja/neo4j-graph-data-science-2.3.1.jar
# Allow Neo4j remote access
#RUN sed -i 's/#dbms.default_listen_address/dbms.default_listen_address/g' /etc/neo4j/neo4j.conf


# Run the data loader script
RUN chmod +x /cse511/data_loader.py && \
    echo "Starting Neo4j for data loading..." && \
    neo4j start && \
    echo "Waiting for Neo4j to be ready..." && \
    sleep 45 && \
    echo "Running data_loader.py..." && \
    python3 /cse511/data_loader.py || (echo "Data loader failed!" && neo4j stop && exit 1) && \
    echo "Data loading script completed, waiting for transaction commit..." && \
    sleep 10 && \
    echo "Performing checkpoint to flush data to disk..." && \
    (echo "CALL db.checkpoint();" | cypher-shell -u neo4j -p graphprocessing || echo "Checkpoint command not available, data should still persist") && \
    sleep 5 && \
    echo "Stopping Neo4j..." && \
    neo4j stop && \
    echo "Neo4j stopped, waiting for clean shutdown..." && \
    sleep 10

# Expose Neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]
