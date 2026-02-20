import csv
import os
import time
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
GTFS_DIR = 'base/data/Export_OpenData_SNCF_GTFS_NewTripId'

BATCH_SIZE = 5000


def load_csv(filename):
    path = os.path.join(GTFS_DIR, filename)
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def batch_import(session, query, data, label=""):
    total = len(data)
    for i in range(0, total, BATCH_SIZE):
        batch = data[i : i + BATCH_SIZE]
        session.execute_write(lambda tx, b=batch: tx.run(query, rows=b))
        done = min(i + BATCH_SIZE, total)
        print(f"  {label} {done}/{total}")


def create_constraints(session):
    print("Creating constraints and indexes...")
    for q in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agency) REQUIRE a.agency_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Stop) REQUIRE s.stop_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trip) REQUIRE t.trip_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (st:StopTime) ON (st.trip_id, st.stop_sequence)",
    ]:
        session.run(q)


def import_agencies(session):
    print("Importing agencies...")
    data = load_csv("agency.txt")
    session.execute_write(
        lambda tx: tx.run(
            """
            UNWIND $rows AS row
            CREATE (a:Agency {
                agency_id: row.agency_id,
                name: row.agency_name,
                url: row.agency_url,
                timezone: row.agency_timezone,
                lang: row.agency_lang
            })
            """,
            rows=data,
        )
    )
    print(f"  {len(data)} agencies imported")


def import_stops(session):
    print("Importing stops...")
    data = load_csv("stops.txt")
    batch_import(
        session,
        """
        UNWIND $rows AS row
        CREATE (s:Stop {
            stop_id: row.stop_id,
            name: row.stop_name,
            lat: toFloat(row.stop_lat),
            lon: toFloat(row.stop_lon),
            location_type: toInteger(row.location_type),
            parent_station: row.parent_station
        })
        """,
        data,
        "stops",
    )

    print("  Creating PART_OF relationships...")
    session.execute_write(
        lambda tx: tx.run(
            """
            MATCH (child:Stop)
            WHERE child.parent_station IS NOT NULL AND child.parent_station <> ''
            MATCH (parent:Stop {stop_id: child.parent_station})
            CREATE (child)-[:PART_OF]->(parent)
            """
        )
    )


def import_routes(session):
    print("Importing routes...")
    data = load_csv("routes.txt")
    batch_import(
        session,
        """
        UNWIND $rows AS row
        MATCH (a:Agency {agency_id: row.agency_id})
        CREATE (r:Route {
            route_id: row.route_id,
            short_name: row.route_short_name,
            long_name: row.route_long_name,
            type: toInteger(row.route_type),
            color: row.route_color
        })
        CREATE (a)-[:OPERATES]->(r)
        """,
        data,
        "routes",
    )


def import_trips(session):
    print("Importing trips...")
    data = load_csv("trips.txt")
    batch_import(
        session,
        """
        UNWIND $rows AS row
        MATCH (r:Route {route_id: row.route_id})
        CREATE (t:Trip {
            trip_id: row.trip_id,
            headsign: row.trip_headsign,
            direction_id: row.direction_id,
            service_id: row.service_id
        })
        CREATE (r)-[:HAS_TRIP]->(t)
        """,
        data,
        "trips",
    )


def import_stop_times(session):
    print("Importing stop_times (this may take a few minutes)...")
    data = load_csv("stop_times.txt")
    batch_import(
        session,
        """
        UNWIND $rows AS row
        MATCH (t:Trip {trip_id: row.trip_id})
        MATCH (s:Stop {stop_id: row.stop_id})
        CREATE (st:StopTime {
            trip_id: row.trip_id,
            arrival: row.arrival_time,
            departure: row.departure_time,
            stop_sequence: toInteger(row.stop_sequence)
        })
        CREATE (t)-[:HAS_STOP_TIME]->(st)
        CREATE (st)-[:AT_STOP]->(s)
        """,
        data,
        "stop_times",
    )


def import_calendar_dates(session):
    print("Importing calendar dates...")
    data = load_csv("calendar_dates.txt")
    batch_import(
        session,
        """
        UNWIND $rows AS row
        MATCH (t:Trip {service_id: row.service_id})
        WITH t, row
        LIMIT 1
        CREATE (sd:ServiceDate {
            service_id: row.service_id,
            date: row.date,
            exception_type: toInteger(row.exception_type)
        })
        """,
        data,
        "calendar_dates",
    )


def create_next_relationships(session):
    print("Creating NEXT relationships between consecutive stop times...")
    print("  (batched to avoid memory issues)")
    session.run(
        """
        CALL apoc.periodic.iterate(
            'MATCH (st1:StopTime) RETURN st1',
            'WITH st1
             MATCH (st2:StopTime {trip_id: st1.trip_id, stop_sequence: st1.stop_sequence + 1})
             CREATE (st1)-[:NEXT]->(st2)',
            {batchSize: 5000, parallel: false}
        )
        """
    )
    print("  NEXT relationships created")


def add_travel_time_weights(session):
    print("Adding travel_time weights on NEXT relationships...")
    print("  (batched to avoid memory issues)")
    session.run(
        """
        CALL apoc.periodic.iterate(
            'MATCH (st1:StopTime)-[r:NEXT]->(st2:StopTime) RETURN st1, st2, r',
            'WITH st1, st2, r
             SET r.travel_time = duration.between(time(st1.departure), time(st2.arrival)).minutes',
            {batchSize: 5000, parallel: false}
        )
        """
    )
    count = session.run(
        "MATCH ()-[r:NEXT]->() WHERE r.travel_time IS NOT NULL RETURN count(r) AS c"
    ).single()["c"]
    print(f"  {count} NEXT relationships now have travel_time")


def create_transfer_relationships(session):
    print("Creating TRANSFER relationships (correspondances)...")
    print("  (this may take a while)")
    session.run(
        """
        CALL apoc.periodic.iterate(
            'MATCH (st1:StopTime)-[:AT_STOP]->(s1:Stop)-[:PART_OF]->(parent:Stop)<-[:PART_OF]-(s2:Stop)<-[:AT_STOP]-(st2:StopTime)
             WHERE st1.trip_id <> st2.trip_id
               AND st2.departure > st1.arrival
             RETURN st1, st2',
            'WITH st1, st2
             WITH st1, st2,
                  duration.between(time(st1.arrival), time(st2.departure)).minutes AS wait
             WHERE wait >= 5 AND wait <= 120
             CREATE (st1)-[:TRANSFER {wait_time: wait}]->(st2)',
            {batchSize: 5000, parallel: false}
        )
        """
    )
    count = session.run(
        "MATCH ()-[r:TRANSFER]->() RETURN count(r) AS c"
    ).single()["c"]
    print(f"  {count} TRANSFER relationships created")


def add_unified_weight(session):
    print("Adding unified 'weight' property on NEXT and TRANSFER relationships...")
    # Parse HH:MM manually to handle GTFS times >= 24:00:00 (next-day service)
    result = session.run(
        """
        CALL apoc.periodic.iterate(
            'MATCH (st1:StopTime)-[r:NEXT]->(st2:StopTime) RETURN st1, st2, r',
            'WITH st1, st2, r,
                  toInteger(substring(st2.arrival, 0, 2)) * 60 + toInteger(substring(st2.arrival, 3, 2))
                  - toInteger(substring(st1.departure, 0, 2)) * 60 - toInteger(substring(st1.departure, 3, 2))
                  AS mins
             SET r.weight = mins',
            {batchSize: 5000, parallel: false}
        )
        YIELD batches, failedBatches
        RETURN batches, failedBatches
        """
    ).single()
    print(f"  NEXT: {result['batches']} batches, {result['failedBatches']} failed")

    result = session.run(
        """
        CALL apoc.periodic.iterate(
            'MATCH (st1:StopTime)-[r:TRANSFER]->(st2:StopTime) RETURN st1, st2, r',
            'WITH st1, st2, r,
                  toInteger(substring(st2.departure, 0, 2)) * 60 + toInteger(substring(st2.departure, 3, 2))
                  - toInteger(substring(st1.arrival, 0, 2)) * 60 - toInteger(substring(st1.arrival, 3, 2))
                  AS mins
             SET r.weight = mins',
            {batchSize: 5000, parallel: false}
        )
        YIELD batches, failedBatches
        RETURN batches, failedBatches
        """
    ).single()
    print(f"  TRANSFER: {result['batches']} batches, {result['failedBatches']} failed")


def create_gds_projection(session):
    print("Creating GDS graph projection...")
    # Drop existing projection if any
    session.run(
        """
        CALL gds.graph.drop('transport', false)
        """
    )
    # Project StopTime nodes with NEXT and TRANSFER relationships using unified weight
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
    count = session.run(
        "CALL gds.graph.list() YIELD graphName, nodeCount, relationshipCount "
        "WHERE graphName = 'transport' "
        "RETURN nodeCount, relationshipCount"
    ).single()
    print(f"  Projected: {count['nodeCount']} nodes, {count['relationshipCount']} relationships")


def find_fastest_path(session, from_stop, to_stop, depart_after="08:00:00"):
    print(f"Finding fastest path (Dijkstra): {from_stop} -> {to_stop} (after {depart_after})...")
    result = session.run(
        """
        MATCH (:Stop {name: $from_stop})<-[:PART_OF]-()<-[:AT_STOP]-(source:StopTime)
        WHERE source.departure >= $depart_after
        WITH source ORDER BY source.departure LIMIT 1

        MATCH (:Stop {name: $to_stop})<-[:PART_OF]-()<-[:AT_STOP]-(target:StopTime)
        WITH source, collect(target) AS targets
        UNWIND targets[..20] AS target

        CALL gds.shortestPath.dijkstra.stream('transport', {
            sourceNode: source,
            targetNode: target,
            relationshipWeightProperty: 'weight'
        })
        YIELD totalCost, path
        WITH totalCost, nodes(path) AS pathNodes, length(path) AS nb_steps
        UNWIND pathNodes AS n
        OPTIONAL MATCH (n)-[:AT_STOP]->(s:Stop)-[:PART_OF]->(p:Stop)
        WITH totalCost, nb_steps, collect(DISTINCT p.name) AS gares,
             collect(DISTINCT n.trip_id) AS trips
        RETURN totalCost, nb_steps, gares, trips
        ORDER BY totalCost
        LIMIT 1
        """,
        from_stop=from_stop,
        to_stop=to_stop,
        depart_after=depart_after,
    )
    record = result.single()
    if record:
        print(f"  Duration: {record['totalCost']} min")
        print(f"  Steps: {record['nb_steps']}")
        print(f"  Trips: {record['trips']}")
        print(f"  Stations: {record['gares']}")
    else:
        print("  No path found")
    return record


def find_fewest_stops(session, from_stop, to_stop, depart_after="08:00:00"):
    print(f"Finding path with fewest stops: {from_stop} -> {to_stop} (after {depart_after})...")
    result = session.run(
        """
        MATCH (fromStop:Stop {name: $from_stop})<-[:PART_OF]-(fp)<-[:AT_STOP]-(source:StopTime)
        WHERE source.departure >= $depart_after
        WITH source ORDER BY source.departure LIMIT 5
        MATCH (toStop:Stop {name: $to_stop})<-[:PART_OF]-(tp)<-[:AT_STOP]-(target:StopTime)
        WITH source, target
        MATCH p = shortestPath((source)-[:NEXT|TRANSFER*]->(target))
        RETURN length(p) AS nb_steps,
               [n IN nodes(p) | [(n)-[:AT_STOP]->(s) | s.name][0]] AS gares,
               [n IN nodes(p) | n.trip_id] AS trips
        ORDER BY nb_steps
        LIMIT 5
        """,
        from_stop=from_stop,
        to_stop=to_stop,
        depart_after=depart_after,
    )
    records = list(result)
    for r in records:
        print(f"  {r['nb_steps']} steps | Stations: {r['gares']}")
    if not records:
        print("  No path found")
    return records


def print_stats(session):
    print("\n--- Import Summary ---")
    result = session.run(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
    )
    for record in result:
        print(f"  {record['label']}: {record['count']}")

    result = session.run(
        "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC"
    )
    for record in result:
        print(f"  -[{record['type']}]->: {record['count']}")

#Groups

def import_all_nodes(session):
    import_agencies(session)
    import_stops(session)
    import_routes(session)
    import_trips(session)
    import_stop_times(session)
    import_calendar_dates(session)

def build_all_relationships(session):
    create_next_relationships(session)
    add_travel_time_weights(session)
    create_transfer_relationships(session)
    add_unified_weight(session)

def main():
    print(f"Connecting to Neo4j at {URI}...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    print("Connected!\n")

    start = time.time()

    with driver.session() as session:
        create_constraints(session)
        
        import_all_nodes(session)
        build_all_relationships(session)
        
        create_gds_projection(session)
        print_stats(session)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")
    driver.close()


if __name__ == "__main__":
    main()
