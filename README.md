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
3. **Access the Streamlit app**
Open your browser and go to:
```arduino
http:localhost:8501
```

# RAG-system-CyberSA
## Prerequisites

Before running the system, ensure that the Turtle file you intend to use is located in the `/rag/files/knowledge_base` directory.

## 🚀 Getting Started
1. **Clone the repository**
```bash
git clone https://github.com/luiigirusso/QA-system-CyberSA.git
cd QA-system-CyberSA
```
2. **Move to the RAG directory**
```bash
cd rag
```
3. **(First run or dataset change only)** Build and launch the components needed to initialize the system:

- These steps are required only the first time you run the system, or if you change the dataset and need to retrain the embeddings.
```bash
# Launch the training component
docker compose -f docker-compose.base.yml up --build

# Launch the embeddings component
docker compose -f docker-compose.embeddings.yml up --build
```

4. **(Subsequent runs)** If the dataset has not changed and the embeddings are already indexed, you can simply start the RAG component:
```bash
# Launch the RAG component
docker compose -f docker-compose.rag.yml up --build
```

5. **Access the Streamlit app**
Open your browser and go to:
```arduino
http:localhost:8502
```

