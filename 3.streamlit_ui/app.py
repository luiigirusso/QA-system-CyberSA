import streamlit as st
import requests
import os
import re
import pickle
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

def format_results(results):
    """
    Formats a list of retrieved entity URIs into a readable string.
    
    Args:
        results (list): A list of entity URIs.
    
    Returns:
        str: A string with each entity formatted as a bullet point.
    """
    formatted = "Search Entities:\n"
    formatted += "\n".join(f"- {entity}" for entity in results)
    return formatted


def format_triples(triples, flag):
    """
    Formats a list of triples into a readable string.

    Args:
        triples (list): A list of triples or groups of triples.
        flag (int): If 0, triples are shown flat. If 1, grouped by entity.
    
    Returns:
        str: A formatted string representation of the triples.
    """
    formatted = "\nTriples:\n"
    if flag == 0:
        formatted += "\n".join(f"- {triple_group}" for triple_group in triples)
    else:
        for triple_group in triples:
            formatted += "\n".join(f"  - {triple[0]} {triple[1]} {triple[2]}" for triple in triple_group)
    return formatted

def extract_name(url):
    """
    Extracts the last part of a URI to get a readable entity name.

    Args:
        url (str): A full URI string.
    
    Returns:
        str: The extracted entity name or the original URL if no match.
    """
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

def search(cypher_query):
    """
    Executes a Cypher query on the Neo4j graph and returns URIs and triples.

    Args:
        cypher_query (str): The Cypher query to execute.
    
    Returns:
        tuple: (uris, triples, original_query)
    """
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

def get_context(response):
    """
    Retrieves contextual triples from the graph or a fallback pickle file.

    Args:
        response (str): Cypher query or raw response text.
    
    Returns:
        tuple: (uris, context_triples, cypher_query)
    """
    context = []
    results, triples, cypher_query = search(response)

    if triples:
        context.extend(triples)
    else:
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

def generate_LLM_answer(question: str):
    """
    Calls the LLM directly for a general answer (outside main pipeline).

    Args:
        question (str): The user's natural language question.
    
    Returns:
        str: The LLM-generated response.
    """
    llm = ChatOpenAI(
        temperature=0,
        api_key=os.getenv("OPENAI_API_TOKEN"),
        model="gpt-4o-mini"
    )
    response = llm.invoke(question)
    return response.content

# --- Streamlit UI ---

st.title("🔒 Security Analyst AI Assistant")
st.write("I am here to help you!")

# Initialize chat message history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user input
if user_input := st.chat_input("Enter your question..."):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Query translation service (NL → Cypher)
    response = requests.post("http://query_translator:8000/translate", json={"question": user_input})
    cypher_query = response.json().get("cypher_query")

    # Retrieve context and triples
    results, context, cypher_query = get_context(cypher_query)

    # Format results
    formatted_context = format_results(results) if results else ""
    formatted_triples = format_triples(context, flag=1 if results else 0)

    # Response generation service
    response = requests.post("http://response_generator:8000/generate", json={"question": user_input, "context": formatted_triples})
    answer = response.json().get("answer", "")

    # Generate LLM-based response
    llm_answer = generate_LLM_answer(user_input)

    # Display AI assistant's main response
    with st.chat_message("assistant"):
        st.markdown(answer)
    
    # Save assistant response to chat history
    st.session_state["messages"].append({"role": "assistant", "content": answer})

    # Expandable sections for additional details
    with st.expander("🔍 Show LLM Answer"):
        st.markdown(llm_answer)

    with st.expander("📚 Show Context"):
        st.markdown(formatted_context + formatted_triples)

    with st.expander("📊 Show Generated Cypher Query"):
        st.code(cypher_query, language="cypher")
