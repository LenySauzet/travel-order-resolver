from neo4j import GraphDatabase
from init_neo4j import create_gds_projection, find_fastest_path, find_fewest_stops

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    # La projection GDS est en mémoire : recréer si Neo4j a redémarré
    create_gds_projection(session)

    print()

    # Test 1: Paris Gare de Lyon -> Lyon Part Dieu (avec correspondance)
    find_fastest_path(session, "Paris Gare de Lyon Hall 1 - 2", "Lyon Part Dieu")

    print()

    find_fewest_stops(session, "Paris Gare de Lyon Hall 1 - 2", "Lyon Part Dieu")

    print()

    # Test 2: Paris Gare de Lyon -> Grenoble (direct TGV)
    find_fastest_path(session, "Paris Gare de Lyon Hall 1 - 2", "Grenoble")

driver.close()
