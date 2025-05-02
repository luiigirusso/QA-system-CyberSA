# QA-system-CyberSA
## Prerequisites

Before running the system, make sure you have the necessary setup:

1. **Install Docker**
   Ensure that [Docker](https://docs.docker.com/get-started/get-docker/) is installed and running on your system.

2. **Install Neo4j Desktop**  
   Download and install [Neo4j Desktop](https://neo4j.com/download/) on your system.

3. **Load the RDF File into Neo4j**  
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

2. **Create the `.env` file**
   Below is an example template — to run the system, you must provide your OpenAI API key and the Neo4j database credentials:
   ```bash
   # Pipeline Information
   PROJECT_PREFIX=qa

   # Knowledge Base
   KB_TURTLE_FILE_PATH=./knowledge_base/lan_v1.5.ttl
   KB_PICKLE_FILE_PATH=./knowledge_base/lan_v1.5.pkl

   # Query Translator
   OPENAI_API_TOKEN=YOUR-OPENAI-KEY

   # Streamlit (Neo4j access)
   NEO4J_URI=bolt://host.docker.internal:7687
   NEO4J_USERNAME=YOUR-NEO4J-USERNAME
   NEO4J_PASSWORD=YOUR-NEO4J-PASSWORD
   ```
   ⚠️ Replace `YOUR-OPENAI-KEY` with your OpenAI API key, `YOUR-NEO4J-USERNAME` with the username of your Neo4j database and `YOUR-NEO4J-PASSWORD` with the password of your Neo4j database,

3. **Build and launch the pipeline**
   ```bash
   docker compose up --build
   ```
4. **Access the Streamlit app**
   Open your browser and go to:
   ```arduino
   http://localhost:8501
   ```

# RAG-system-CyberSA
## Prerequisites
+ Docker is installed and running on your machine.
+ The Turtle file (.ttl) you intend to use is placed in the `/rag/files/knowledge_base` directory.

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
3. **(First run or dataset change only)** Create the `.env` file in the `rag` directory.
   Below is an example you can use as a template — you only need to set your OpenAI API key for the system to work:
   ```bash
   # Pipeline Information
   PROJECT_PREFIX=rag

   # Knowledge Base
   KB_TURTLE_FILE_PATH=./knowledge_base/lan_v1.5.ttl
   KB_PICKLE_FILE_PATH=./knowledge_base/lan_v1.5.pkl

   # Training
   EMBEDDING_DIM=1536
   NUM_EPOCHS=580
   LEARNING_RATE=0.05398028996737351
   NUM_NEGS_PER_POS=36
   MODEL=TransE
   OPTIMIZER=Adagrad
   BATCH_SIZE=16
   MODEL_PATH=./training/TransE.pkl

   # Embeddings
   OPENAI_API_TOKEN=YOUR-API-KEY
   ENTITY_EMBEDDINGS_PATH=./embeddings/entity_embeddings.pkl
   RELATION_EMBEDDINGS_PATH=./embeddings/relation_embeddings.pkl
   ```
   ⚠️ Replace `YOUR-API-KEY` with your actual OpenAI API key.

4. **(First run or dataset change only)** Build and launch the components needed to initialize the system:

   These steps are required only the first time you run the system, or if you change the dataset and need to retrain the embeddings.
   ```bash
   # Launch the training component
   docker compose -f docker-compose.base.yml up --build

   # Launch the embeddings component
   docker compose -f docker-compose.embeddings.yml up --build
   ```

5. **Launch RAG component** If the dataset has not changed and the embeddings are already indexed, you can simply start the RAG component:
   ```bash
   # Launch the RAG component
   docker compose -f docker-compose.rag.yml up --build
   ```

6. **Access the Streamlit app**
   Open your browser and go to:
   ```arduino
   http://localhost:8502
   ```

