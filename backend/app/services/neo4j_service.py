from neo4j import GraphDatabase

from ..core.config import config


class Neo4jService:
    _instance: "Neo4jService | None" = None

    def __init__(self):
        self._driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_user, config.neo4j_password),
        )
        self._driver.verify_connectivity()
        self._ensure_gds_projection()

    @classmethod
    def get_instance(cls) -> "Neo4jService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def close(self):
        self._driver.close()

    def _ensure_gds_projection(self):
        with self._driver.session() as session:
            exists = session.run(
                "CALL gds.graph.list() YIELD graphName "
                "WHERE graphName = 'transport' "
                "RETURN count(*) AS c"
            ).single()["c"]
            if exists == 0:
                session.run(
                    """
                    CALL gds.graph.project(
                        'transport',
                        'StopTime',
                        {
                            NEXT: {
                                type: 'NEXT',
                                properties: 'weight'
                            },
                            TRANSFER: {
                                type: 'TRANSFER',
                                properties: 'weight'
                            }
                        }
                    )
                    """
                )

    def fastest_path(self, from_stop: str, to_stop: str, depart_after: str = "08:00:00") -> dict | None:
        with self._driver.session() as session:
            dest_ids = session.run(
                """
                MATCH (:Stop {name: $to_stop})<-[:PART_OF]-()<-[:AT_STOP]-(st:StopTime)
                WHERE st.stop_sequence > 0
                RETURN collect(id(st)) AS ids
                """,
                to_stop=to_stop,
            ).single()["ids"]

            result = session.run(
                """
                MATCH (:Stop {name: $from_stop})<-[:PART_OF]-()<-[:AT_STOP]-(source:StopTime)
                WHERE source.departure >= $depart_after
                WITH source ORDER BY source.departure LIMIT 10

                CALL gds.shortestPath.dijkstra.stream('transport', {
                    sourceNode: source,
                    targetNodes: [n IN gds.util.asNodes($dest_ids) | n],
                    relationshipWeightProperty: 'weight'
                })
                YIELD totalCost, path
                WITH source, totalCost, nodes(path) AS pathNodes, length(path) AS nb_steps
                UNWIND pathNodes AS n
                OPTIONAL MATCH (n)-[:AT_STOP]->(s:Stop)-[:PART_OF]->(p:Stop)
                WITH source, totalCost, nb_steps,
                     collect(DISTINCT p.name) AS gares,
                     collect(DISTINCT n.trip_id) AS trips
                RETURN totalCost, nb_steps, gares, trips
                ORDER BY totalCost
                LIMIT 1
                """,
                from_stop=from_stop,
                depart_after=depart_after,
                dest_ids=dest_ids,
            )
            record = result.single()
            if record is None:
                return None
            return {
                "totalCost": record["totalCost"],
                "nb_steps": record["nb_steps"],
                "stations": record["gares"],
                "trips": record["trips"],
            }

    def fewest_stops(self, from_stop: str, to_stop: str, depart_after: str = "08:00:00") -> list[dict]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (:Stop {name: $from_stop})<-[:PART_OF]-()<-[:AT_STOP]-(source:StopTime)
                WHERE source.departure >= $depart_after
                WITH source ORDER BY source.departure LIMIT 10

                MATCH (:Stop {name: $to_stop})<-[:PART_OF]-()<-[:AT_STOP]-(target:StopTime)
                WHERE target.arrival > source.departure
                  AND target.stop_sequence > 0
                WITH source, target
                ORDER BY target.arrival
                WITH source, collect(target)[..200] AS targets
                UNWIND targets AS target

                MATCH p = shortestPath((source)-[:NEXT|TRANSFER*..100]->(target))
                RETURN length(p) AS nb_steps,
                       [n IN nodes(p) | [(n)-[:AT_STOP]->(s) | s.name][0]] AS gares,
                       [n IN nodes(p) | n.trip_id] AS trips,
                       size([r IN relationships(p) WHERE type(r) = 'TRANSFER']) AS nb_transfers,
                       reduce(cost = 0.0, r IN relationships(p) | cost + r.weight) AS totalCost
                ORDER BY nb_steps
                LIMIT 5
                """,
                from_stop=from_stop,
                to_stop=to_stop,
                depart_after=depart_after,
            )
            return [
                {
                    "nb_steps": r["nb_steps"],
                    "nb_transfers": r["nb_transfers"],
                    "stations": r["gares"],
                    "trips": r["trips"],
                    "duration_minutes": r["totalCost"],
                }
                for r in result
            ]
