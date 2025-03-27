import os
import random
import pickle
import rdflib
from rdflib.plugin import PluginException

def parse_rdf(file_path):
    """Parses an RDF file in Turtle format and returns a list of triples."""
    g = rdflib.Graph()
    try:
        g.parse(file_path, format='ttl')
    except (PluginException, FileNotFoundError) as e:
        print(f"Error parsing RDF file '{file_path}': {e}")
        return []
    return [(str(s), str(p), str(o)) for s, p, o in g]

def split_triples(triples, train_ratio=0.8, valid_ratio=0.1):
    """Splits triples into training, validation, and test sets."""
    random.shuffle(triples)
    num_triples = len(triples)
    
    train_size = int(train_ratio * num_triples)
    valid_size = int(valid_ratio * num_triples)
    test_size = num_triples - train_size - valid_size
    
    return triples[:train_size], triples[train_size:train_size + valid_size], triples[train_size + valid_size:]

def knowledge_base():
    """Loads an RDF knowledge base, splits it into datasets, and saves them."""
    input_path = os.getenv('KB_TURTLE_FILE_PATH')
    output_path = os.getenv('KB_PICKLE_FILE_PATH')
    
    if not input_path or not os.path.exists(input_path):
        print("Error: RDF input file path is not defined or does not exist.")
        return
    if not output_path:
        print("Error: Output file path is not defined.")
        return
    
    rdf_triples = parse_rdf(input_path)
    if not rdf_triples:
        print("No triples found. Exiting.")
        return
    
    train_triples, valid_triples, test_triples = split_triples(rdf_triples)
    
    print(f'Number of triples in the training set: {len(train_triples)}')
    print(f'Number of triples in the validation set: {len(valid_triples)}')
    print(f'Number of triples in the test set: {len(test_triples)}')
    
    with open(output_path, 'wb') as f:
        pickle.dump((train_triples, valid_triples, test_triples), f)

if __name__ == "__main__":
    knowledge_base()
