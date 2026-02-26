from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def bfs(self, start_node, last_node):
        query = """
        MATCH (start:Location {name: $start}), (end:Location {name: $end})
        MATCH p = shortestPath((start)-[:TRIP*]->(end))
        WITH [n IN nodes(p) | {name: n.name}] AS path
        RETURN [{path: path}] AS result
        """
        params = {"start": int(start_node), "end": int(last_node)}

        with self._driver.session() as session:
            record = session.run(query, params).single()
            return record["result"] if record and record["result"] else []


    def pagerank(self, max_iterations, weight_property):
        gname = "graph1"
        params = {
            "graph_name": gname,
            "weight": weight_property,
            "max_iter": int(max_iterations)
        }

        query_create = """
        CALL gds.graph.project(
            $graph_name,
            'Location',
            {TRIP: {orientation: 'NATURAL', properties: $weight}}
        )
        """

        query_pagerank = """
        CALL gds.pageRank.stream($graph_name, {
            dampingFactor: 0.85,
            maxIterations: $max_iter,
            relationshipWeightProperty: $weight
        })
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS n, score
        RETURN n.name AS name, score
        ORDER BY score DESC
        """

        query_drop = "CALL gds.graph.drop($graph_name, false)"

        with self._driver.session() as session:
            try:
                session.run(query_drop, params)
            except:
                pass

            session.run(query_create, params)
            result = session.run(query_pagerank, params).data()
            try:
                session.run(query_drop, params)
            except:
                pass

        if not result:
            return []

        return [
            {"name": result[0]["name"], "score": result[0]["score"]},
            {"name": result[-1]["name"], "score": result[-1]["score"]}
        ]


