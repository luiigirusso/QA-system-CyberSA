import streamlit as st
import requests
import os
import re
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
import pickle



def format_similarity_results(results):
    formatted = "Similarity Search Entities:\n"
    
    for entity in results:
        formatted += f"- {entity}\n"
    
    return formatted

def format_triples(triples, flag):
    formatted = "\nTriples:\n"
    for triple_group in triples:
        if flag == 0:
            formatted += f"- {triple_group}\n"
        else:
            for triple in triple_group:
                formatted += f"  - {triple[0]} {triple[1]} {triple[2]}\n"
    
    return formatted

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

def search(cypher_query):
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    NEO4J_DATABASE = 'neo4j'
    
    kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
    )
    result = kg.query(cypher_query)
    uris = []
    triples = []

    for entry in result:
        if 'subject' in entry and 'predicate' in entry and 'object' in entry:
            triples.append((extract_name(entry['subject']), extract_name(entry['predicate']), extract_name(entry['object'])))
        elif 'uri' in entry:
            uris.append(entry['uri'])

    return uris,triples, cypher_query

def get_context(response):
    context = []
    results, triples, cypher_query = search(response)
    if triples:
        for triple in triples:
            context.append((triple))
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
                if triple[0] == extract_name(entity_name) or triple[2] == extract_name(entity_name) 
            ]

            # Aggiunge i risultati al contesto
            context.append((filtered_triples))

    return results,context,cypher_query

def generate_LLM_answer(question: str):
    llm = ChatOpenAI(
        temperature=0,
        api_key=os.getenv("OPENAI_API_TOKEN"),
        model_name="gpt-4o-mini"
    )
    response = llm.invoke(question)
    return response.content



st.title("🔒 Security Analyst AI Assistant")
st.write("I am here to help you!")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Enter your question..."):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    response = requests.post("http://query_translator:8000/translate", json={"question": user_input})
    cypher_query = response.json().get("cypher_query")
    context, triples, cypher_query = get_context(cypher_query)

    flag = 0
    if context:
        formatted_context = format_similarity_results(context)
        flag = 1
    else:
        formatted_context = ""
    formatted_triples = format_triples(triples, flag)
    
    flag = 0
    if context:
        formatted_context = format_similarity_results(context)
        flag = 1
    else:
        formatted_context = ""
    formatted_triples = format_triples(triples, flag)


    response = requests.post("http://response_generator:8000/generate", json={"question": user_input, "context": formatted_triples})
    answer = response.json().get("answer", "")

    llm_answer = generate_LLM_answer(user_input)
    
    with st.chat_message("assistant"):
        st.markdown(f"{answer}")
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    
    with st.expander("🔍 Show LLM Answer"):
        st.markdown(llm_answer)
    
    with st.expander("📚 Show Context"):
        st.markdown(formatted_context + formatted_triples)
    
    with st.expander("📊 Show Generated Cypher Query"):
        st.code(cypher_query, language="cypher")
