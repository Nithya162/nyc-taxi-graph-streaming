import pyarrow.parquet as pq
import pandas as pd
from neo4j import GraphDatabase
import time


class DataLoader:

    def __init__(self, uri, user, password):
        """
        Connect to the Neo4j database and other init steps
        
        Args:
            uri (str): URI of the Neo4j database
            user (str): Username of the Neo4j database
            password (str): Password of the Neo4j database
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()


    def close(self):
        """
        Close the connection to the Neo4j database
        """
        self.driver.close()


    # Define a function to create nodes and relationships in the graph
    def load_transform_file(self, file_path):
        """
        Load the parquet file and transform it into a csv file
        Then load the csv file into neo4j

        Args:
            file_path (str): Path to the parquet file to be loaded
        """

        # Read the parquet file
        trips = pq.read_table(file_path)
        trips = trips.to_pandas()

        # Some data cleaning and filtering
        trips = trips[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']]

        # Filter out trips that are not in bronx
        bronx = [3, 18, 20, 31, 32, 46, 47, 51, 58, 59, 60, 69, 78, 81, 94, 119, 126, 136, 147, 159, 167, 168, 169, 174, 182, 183, 184, 185, 199, 200, 208, 212, 213, 220, 235, 240, 241, 242, 247, 248, 250, 254, 259]
        trips = trips[trips.iloc[:, 2].isin(bronx) & trips.iloc[:, 3].isin(bronx)]
        trips = trips[trips['trip_distance'] > 0.1]
        trips = trips[trips['fare_amount'] > 2.5]

        # Convert date-time columns to supported format (ISO 8601 with T separator)
        trips['tpep_pickup_datetime'] = pd.to_datetime(trips['tpep_pickup_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
        trips['tpep_dropoff_datetime'] = pd.to_datetime(trips['tpep_dropoff_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Convert to csv and store in the current directory
        csv_filename = file_path.split(".")[0] + '.csv'
        save_loc = "/var/lib/neo4j/import/" + csv_filename
        trips.to_csv(save_loc, index=False)
        
        print(f"CSV saved to {save_loc}")
        print(f"Number of trips to load: {len(trips)}")

        # Load data into Neo4j using the CSV file
        with self.driver.session() as session:
            # First, create a constraint for unique Location nodes
            try:
                session.run("""
                    CREATE CONSTRAINT location_name IF NOT EXISTS
                    FOR (l:Location) REQUIRE l.name IS UNIQUE
                """)
                print("Constraint created")
            except Exception as e:
                print(f"Constraint creation note: {e}")
            
            # Load the CSV and create nodes and relationships
            query = """
            LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row
            MERGE (pickup:Location {{name: toInteger(row.PULocationID)}})
            MERGE (dropoff:Location {{name: toInteger(row.DOLocationID)}})
            CREATE (pickup)-[:TRIP {{
                distance: toFloat(row.trip_distance),
                fare: toFloat(row.fare_amount),
                pickup_dt: datetime(row.tpep_pickup_datetime),
                dropoff_dt: datetime(row.tpep_dropoff_datetime)
            }}]->(dropoff)
            """.format(csv_file=csv_filename)
            
            print("Executing LOAD CSV query...")
            result = session.run(query)
            summary = result.consume()
            print(f"Nodes created: {summary.counters.nodes_created}")
            print(f"Relationships created: {summary.counters.relationships_created}")
            print("Data loaded successfully!")


def main():

    total_attempts = 10
    attempt = 0

    # The database takes some time to starup!
    # Try to connect to the database 10 times
    while attempt < total_attempts:
        try:
            print(f"Attempt {attempt+1}/{total_attempts} to connect to Neo4j...")
            data_loader = DataLoader("neo4j://localhost:7687", "neo4j", "graphprocessing")
            data_loader.load_transform_file("yellow_tripdata_2022-03.parquet")
            data_loader.close()
            
            print("Data loading completed successfully!")
            attempt = total_attempts

        except Exception as e:
            print(f"(Attempt {attempt+1}/{total_attempts}) Error: ", e)
            attempt += 1
            if attempt < total_attempts:
                print("Waiting 10 seconds before retry...")
                time.sleep(10)


if __name__ == "__main__":
    main()