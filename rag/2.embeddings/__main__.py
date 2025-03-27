import os
import re
import torch
import numpy as np
import json
import pickle
from pykeen.triples import TriplesFactory
from sklearn.linear_model import LinearRegression
from langchain_openai import OpenAIEmbeddings

def extract_name(url):
    prefixes = [
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/2000/01/rdf-schema#",
        "http://example.org/stix#",
        "http://d3fend.mitre.org/ontologies/d3fend.owl#",
        "http://example.org/network#",
        "http://www.w3.org/2002/07/owl#",
        "http://www.w3.org/2004/02/skos/core#",
        "http://example.org/entities/"
    ]
    for prefix in prefixes:
        if url.startswith(prefix):
            return re.split(r'[#/]', url)[-1]
    return url

def normalize_vector(v):
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v

def write_to_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def embeddings():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    model_path = os.getenv('MODEL_PATH')

    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError("Model file path is not defined or does not exist.")

    with open(model_path, 'rb') as file:
        model = pickle.load(file)
    model = model.to(device)

    entity_embeddings = model.entity_representations[0](indices=None).detach().cpu().numpy()
    relation_embeddings = model.relation_representations[0](indices=None).detach().cpu().numpy()

    kb_pickle_file = os.getenv('KB_PICKLE_FILE_PATH')
    if not kb_pickle_file or not os.path.exists(kb_pickle_file):
        raise FileNotFoundError("Knowledge base pickle file path is not defined or does not exist.")

    with open(kb_pickle_file, 'rb') as f:
        train_triples, valid_triples, test_triples = pickle.load(f)

    all_triples = np.array(train_triples + valid_triples + test_triples)
    triples_factory = TriplesFactory.from_labeled_triples(all_triples)
    
    entity_to_id = triples_factory.entity_to_id
    relation_to_id = triples_factory.relation_to_id
    
    entity_embeddings_dict = {entity: entity_embeddings[idx].tolist() for entity, idx in entity_to_id.items()}
    relation_embeddings_dict = {relation: relation_embeddings[idx].tolist() for relation, idx in relation_to_id.items()}
    
    embedding_model = OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_TOKEN"),
        model="text-embedding-ada-002",
    )
    entity_embeddings_openai = embedding_model.embed_documents(list(entity_to_id.keys()))
    relation_embeddings_openai = embedding_model.embed_documents(list(relation_to_id.keys()))
    
    entity_embeddings_dict_openai = {key: embedding for key, embedding in zip(entity_to_id.keys(), entity_embeddings_openai)}
    relation_embeddings_dict_openai = {key: embedding for key, embedding in zip(relation_to_id.keys(), relation_embeddings_openai)}
    
    common_entities = set(entity_embeddings_dict.keys()) & set(entity_embeddings_dict_openai.keys())
    transE_entity_vectors = np.array([normalize_vector(entity_embeddings_dict[e]) for e in common_entities])
    openai_entity_vectors = np.array([normalize_vector(entity_embeddings_dict_openai[e]) for e in common_entities])
    
    reg_entity = LinearRegression()
    reg_entity.fit(transE_entity_vectors, openai_entity_vectors)
    aligned_entity_dict = {entity: (transE_entity_vectors[i] @ reg_entity.coef_.T).tolist() for i, entity in enumerate(common_entities)}
    write_to_file(os.getenv("ENTITY_EMBEDDINGS_PATH"), aligned_entity_dict)
    print("Entity embeddings aligned and saved!")
    
    common_relations = set(relation_embeddings_dict.keys()) & set(relation_embeddings_dict_openai.keys())
    transE_relation_vectors = np.array([normalize_vector(relation_embeddings_dict[r]) for r in common_relations])
    openai_relation_vectors = np.array([normalize_vector(relation_embeddings_dict_openai[r]) for r in common_relations])
    
    reg_relation = LinearRegression()
    reg_relation.fit(transE_relation_vectors, openai_relation_vectors)
    aligned_relation_dict = {relation: (transE_relation_vectors[i] @ reg_relation.coef_.T).tolist() for i, relation in enumerate(common_relations)}
    write_to_file(os.getenv("RELATION_EMBEDDINGS_PATH"), aligned_relation_dict)
    print("Relation embeddings aligned and saved!")

if __name__ == "__main__":
    embeddings()
