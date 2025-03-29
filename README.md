# QA-system-CyberSA
## Prerequisites

Before running the system, make sure you have the necessary setup:

1. **Install Neo4j Desktop**  
   Download and install [Neo4j Desktop](https://neo4j.com/download/) on your system.

2. **Load the RDF File into Neo4j**  
   Open the Neo4j Browser and execute the following commands to load the RDF data:

   ```cypher
   MATCH (n) DETACH DELETE n;

   CALL n10s.graphconfig.init();
   CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
   CALL n10s.rdf.import.fetch('filepath/to/turtle_file.ttl', 'Turtle');

Replace `filepath/to/turtle_file.ttl` with the actual path to your RDF file.

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/luiigirusso/QA-system-CyberSA.git
cd QA-system-CyberSA
```

2. **Build and launch the pipeline**
```bash
docker compose up --build
```
3. **Go to the Streamlit app**

```arduino
http:localhost:8501
```
