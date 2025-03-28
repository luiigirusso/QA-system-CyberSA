import streamlit as st
import requests
import os
import re
import pickle
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

def format_results(results):
    formatted = "Search Entities:\n"
    formatted += "\n".join(f"- {entity}" for entity in results)
    return formatted

# Function to format retrieved triples
def format_triples(triples, flag):
    formatted = "\nTriples:\n"
    if flag == 0:
        formatted += "\n".join(f"- {triple_group}" for triple_group in triples)
    else:
        for triple_group in triples:
            formatted += "\n".join(f"  - {triple[0]} {triple[1]} {triple[2]}" for triple in triple_group)
    return formatted

# Function to extract entity names from URIs
def extract_name(url):
    prefixes = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/2000/01/rdf-schema#",
        "http://example.org/stix#",
        "http://d3fend.mitre.org/ontologies/d3fend.owl#",
        "http://example.org/network#",
        "http://www.w3.org/2002/07/owl#",
        "http://www.w3.org/2004/02/skos/core#"
    ]
    for prefix in prefixes:
        if url.startswith(prefix):
            return re.split(r'[#/]', url)[-1]
    return url

# Function to execute a Cypher query on the Neo4j graph database
def search(cypher_query):
    kg = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        database="neo4j"
    )
    
    result = kg.query(cypher_query)
    uris, triples = [], []

    for entry in result:
        if all(key in entry for key in ("subject", "predicate", "object")):
            triples.append((extract_name(entry["subject"]), extract_name(entry["predicate"]), extract_name(entry["object"])))
        elif "uri" in entry:
            uris.append(entry["uri"])

    return uris, triples, cypher_query

# Function to retrieve context based on query response
def get_context(response):
    context = []
    results, triples, cypher_query = search(response)

    if triples:
        context.extend(triples)
    else:
        # Load precomputed triples from a pickle file
        with open(os.getenv("KB_PICKLE_FILE_PATH"), "rb") as f:
            train_triples, valid_triples, test_triples = pickle.load(f)

        all_triples = train_triples + valid_triples + test_triples

        processed_triples = [
            (extract_name(triple[0]), extract_name(triple[1]), extract_name(triple[2])) 
            for triple in all_triples
        ]

        for entity_name in results:
            filtered_triples = [
                triple for triple in processed_triples
                if extract_name(entity_name) in (triple[0], triple[2])
            ]
            context.append(filtered_triples)

    return results, context, cypher_query

# Function to generate an answer using an LLM
def generate_LLM_answer(question: str):
    llm = ChatOpenAI(
        temperature=0,
        api_key=os.getenv("OPENAI_API_TOKEN"),
        model="gpt-4o-mini"
    )
    response = llm.invoke(question)
    return response.content

# Streamlit UI
st.title("🔒 Security Analyst AI Assistant")
st.write("I am here to help you!")

# Initialize message history if not present
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display previous messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if user_input := st.chat_input("Enter your question..."):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call query translation service
    response = requests.post("http://query_translator:8000/translate", json={"question": user_input})
    cypher_query = response.json().get("cypher_query")

    # Retrieve context and triples
    results, context, cypher_query = get_context(cypher_query)

    # Format results for display
    formatted_context = format_results(results) if results else ""
    formatted_triples = format_triples(context, flag=1 if results else 0)

    # Call response generation service
    response = requests.post("http://response_generator:8000/generate", json={"question": user_input, "context": formatted_triples})
    answer = response.json().get("answer", "")

    # Generate LLM-based response
    llm_answer = generate_LLM_answer(user_input)

    # Display the AI assistant's response
    with st.chat_message("assistant"):
        st.markdown(answer)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})

    # Expandable sections for additional details
    with st.expander("🔍 Show LLM Answer"):
        st.markdown(llm_answer)

    with st.expander("📚 Show Context"):
        st.markdown(formatted_context + formatted_triples)

    with st.expander("📊 Show Generated Cypher Query"):
        st.code(cypher_query, language="cypher")
