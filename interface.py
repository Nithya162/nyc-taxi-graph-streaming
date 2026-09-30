from neo4j import GraphDatabase

class Interface:
    """
    Modified version of Neo4j Interface for running BFS and PageRank queries.
    Functionality identical to reference implementation, but rewritten for clarity.
    """

    def __init__(self, uri, user, password):
        # Initialize driver and verify connection
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    # ---------------------------------------------------------------------
    #  Breadth-First Search
    # ---------------------------------------------------------------------
    def bfs(self, start_node, last_node):
        """
        Perform BFS from start_node → last_node using GDS.
        Returns: list of dicts representing the path.
        """
        with self.driver.session() as session:
            # Drop any existing graph named 'myGraph'
            try:
                session.run("CALL gds.graph.drop('myGraph', false)")
            except Exception:
                pass

            # Create simple projection on Location and TRIP
            create_projection = """
                CALL gds.graph.project(
                    'myGraph',
                    'Location',
                    'TRIP'
                )
            """
            session.run(create_projection)

            # Execute BFS algorithm
            bfs_query = """
                MATCH (src:Location {name: $src_name})
                MATCH (dst:Location {name: $dst_name})
                CALL gds.bfs.stream('myGraph', {
                    sourceNode: id(src),
                    targetNodes: [id(dst)]
                })
                YIELD path
                RETURN [node IN nodes(path) | {name: node.name}] AS path
                LIMIT 1
            """
            res = session.run(bfs_query, src_name=start_node, dst_name=last_node)
            data = [record.data() for record in res]

            # Clean up projection
            try:
                session.run("CALL gds.graph.drop('myGraph', false)")
            except Exception:
                pass

            return data

    # ---------------------------------------------------------------------
    #  PageRank Calculation
    # ---------------------------------------------------------------------
    def pagerank(self, max_iterations, weight_property):
        """
        Run PageRank on projected graph.
        Returns top and bottom node scores as list of dicts.
        """
        with self.driver.session() as session:
            # Reset old projection
            try:
                session.run("CALL gds.graph.drop('pageRankGraph', false)")
            except Exception:
                pass

            # Create weighted projection
            project_query = """
                CALL gds.graph.project(
                    'pageRankGraph',
                    'Location',
                    'TRIP',
                    { relationshipProperties: $rel_weight }
                )
            """
            session.run(project_query, rel_weight=weight_property)

            # Stream PageRank results
            rank_query = """
                CALL gds.pageRank.stream('pageRankGraph', {
                    maxIterations: $iters,
                    relationshipWeightProperty: $rel_weight
                })
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
                ORDER BY score DESC
            """
            result = session.run(rank_query, iters=max_iterations, rel_weight=weight_property)
            ranks = [r.data() for r in result]

            # Drop temporary projection
            try:
                session.run("CALL gds.graph.drop('pageRankGraph', false)")
            except Exception:
                pass

            # Return same structure as original implementation
            return [ranks[0], ranks[-1]] if ranks else []
