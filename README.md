# Graph Analytics Pipeline: From Docker to Distributed Stream Processing

A two-phase graph analytics platform built on the NYC yellow taxi dataset, evolving from a containerized proof-of-concept into a distributed, streaming, production-style architecture.

## Overview

This project models NYC taxi trips as a graph — taxi zones are nodes, and trips between zones are edges — and runs graph algorithms (PageRank, BFS) to analyze transportation patterns. The system is built in two phases that mirror a real-world architectural evolution:

- **Phase 1:** A reproducible, containerized environment using Docker and Neo4j to validate the data model and run graph algorithms.
- **Phase 2:** A distributed, event-driven architecture using Apache Kafka, Kafka Connect, and Kubernetes to support real-time streaming ingestion at scale.

## Tech Stack

- **Graph Database:** Neo4j (with the Graph Data Science library for PageRank and BFS)
- **Containerization:** Docker
- **Orchestration:** Kubernetes (via Minikube), Helm
- **Streaming:** Apache Kafka (Confluent Platform), Kafka Connect, Apache Zookeeper
- **Data Processing:** Python, Pandas, PyArrow

## Architecture

**Phase 1 — Dockerized Graph Processing**
NYC taxi data (Parquet format) is cleaned and loaded into a Dockerized Neo4j instance. `data_loader.py` filters and transforms the raw data, then loads it into Neo4j as `Location` nodes and `TRIP` relationships. PageRank identifies high-activity transportation hubs; BFS finds shortest paths between locations.

**Phase 2 — Kubernetes Streaming Architecture**
The pipeline is decomposed into independent services running on Kubernetes. A Python producer (`data_producer.py`) publishes trip events to a Kafka topic in real time. Kafka Connect declaratively sinks these events into Neo4j using idempotent Cypher `MERGE` operations, so the graph updates live as new data streams in.

## Results

- Processed ~50,000 taxi trips into a graph of 873 `TRIP` relationships
- Single-hop graph queries: under 100ms; multi-hop traversals: 200–500ms
- Kafka streaming throughput: 10–20 messages/second with zero message loss
- End-to-end latency (Kafka publish → Neo4j commit): 1–2 seconds
- Kubernetes pod failures recovered automatically with no data loss

## Files

- `interface.py` — [describe what this does]
- `Dockerfile` — container definition for the Phase 1 environment
- `data_loader.py` — ingestion and preprocessing pipeline for the NYC taxi dataset

## Course Context

Developed as the course project for **CSE 511: Data Processing at Scale**, Arizona State University.
