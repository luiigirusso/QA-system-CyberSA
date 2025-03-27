import os
import torch
import pickle
import numpy as np
import pykeen.models
from pykeen.training import SLCWATrainingLoop
from pykeen.sampling import BasicNegativeSampler
from pykeen.triples import TriplesFactory
from pykeen.optimizers import optimizer_resolver

def train():
    # Select the device (GPU if available, otherwise CPU)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Load hyperparameters from environment variables
    try:
        embedding_dim = int(os.getenv('EMBEDDING_DIM', 1536))
        num_epochs = int(os.getenv('NUM_EPOCHS', 100))
        learning_rate = float(os.getenv('LEARNING_RATE', 0.01))
        num_negs_per_pos = int(os.getenv('NUM_NEGS_PER_POS', 1))
        model_name = os.getenv('MODEL', 'TransE')
        optimizer_name = os.getenv('OPTIMIZER', 'Adagrad')
        batch_size = int(os.getenv('BATCH_SIZE', 16))
    except ValueError as e:
        print(f"Error parsing hyperparameters: {e}")
        return

    kb_pickle_file = os.getenv('KB_PICKLE_FILE_PATH')
    if not kb_pickle_file or not os.path.exists(kb_pickle_file):
        print("Error: Knowledge base pickle file path is not defined or does not exist.")
        return
    
    # Load dataset
    with open(kb_pickle_file, 'rb') as f:
        try:
            train_triples, valid_triples, test_triples = pickle.load(f)
        except (pickle.UnpicklingError, ValueError) as e:
            print(f"Error loading dataset: {e}")
            return
    
    # Combine all triples into a single dataset
    all_triples = train_triples + valid_triples + test_triples
    train_triples_np = np.array(all_triples)
    train_tf = TriplesFactory.from_labeled_triples(train_triples_np)
    
    # Get the model class dynamically from PyKEEN
    try:
        model_class = getattr(pykeen.models, model_name)
    except AttributeError:
        print(f"Error: Model '{model_name}' not found in PyKEEN.")
        return

    # Initialize the knowledge graph embedding model
    model = model_class(
        triples_factory=train_tf,
        embedding_dim=embedding_dim,
        random_seed=42,
        loss='MarginRankingLoss',
    ).to(device)
    
    # Configure negative sampling
    negative_sampler = BasicNegativeSampler(
        mapped_triples=train_tf.mapped_triples,
        num_negs_per_pos=num_negs_per_pos
    )
    
    # Resolve optimizer
    optimizer_class = optimizer_resolver.lookup(optimizer_name)
    optimizer = optimizer_class(params=model.parameters(), lr=learning_rate)
    
    # Set up the training loop
    training_loop = SLCWATrainingLoop(
        triples_factory=train_tf,
        model=model,
        optimizer=optimizer,
        negative_sampler=negative_sampler,
    )
    
    # Training parameters
    checkpoint_directory = './training'
    checkpoint_frequency = 10
    
    # Train the model
    training_loop.train(
        triples_factory=train_tf,
        num_epochs=num_epochs,
        checkpoint_name=os.getenv('CHECKPOINT_NAME'),
        checkpoint_directory=checkpoint_directory,
        batch_size=batch_size,
        checkpoint_frequency=checkpoint_frequency,
    )
    
    # Save the trained model
    model_path = os.getenv('MODEL_PATH')
    with open(model_path, 'wb') as file:
        pickle.dump(model, file)
    
    return model

# Run training if the script is executed directly
if __name__ == "__main__":
    model = train()
