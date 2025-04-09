import os
import numpy as np
import pickle
import torch
from pykeen.triples import TriplesFactory
from pykeen.models import Model
from pykeen.predict import predict_target
from dotenv import load_dotenv
load_dotenv(".env")

with open(os.getenv("KB_PICKLE_FILE"), 'rb') as f:
    train_triples, valid_triples, test_triples = pickle.load(f)

all_triples = train_triples + valid_triples + test_triples
all_triples_np = np.array(all_triples)
triples_factory = TriplesFactory.from_labeled_triples(all_triples_np)

entity_to_id = triples_factory.entity_to_id
relation_to_id = triples_factory.relation_to_id

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_path = os.getenv("MODEL_PATH")

with open(model_path, 'rb') as file:
    model: Model = pickle.load(file)
model.to(device)

test_groups = {
    "network_structure": [
        ("http://example.org/network#LAN1", "http://example.org/network#contains", "http://example.org/network#POP3Server1", "both"),
        ("http://example.org/network#Laptop1", "http://example.org/network#wireless_connection", "http://example.org/network#WirelessAP", "head"),
        ("http://example.org/network#Laptop2", "http://example.org/network#wireless_connection", "http://example.org/network#WirelessAP", "head"),
        ("http://example.org/network#Desktop1", "http://example.org/network#wireless_connection", "http://example.org/network#WirelessAP", "head"),
        ("http://example.org/network#Mobile", "http://example.org/network#wireless_connection", "http://example.org/network#WirelessAP", "head"),
        ("http://example.org/network#Remote", "http://example.org/network#contains", "http://example.org/network#VPNServer", "head"),
    ],
    "description": [
        ("http://example.org/stix#OSExhaustionFlood", "http://example.org/stix#impact-type", "Availability", "tail"),
        ("http://example.org/stix#DirectNetworkFlood", "http://example.org/stix#impacts", "http://d3fend.mitre.org/ontologies/d3fend.owl#Server", "tail"),
        ("http://example.org/stix#Industroyer", "http://example.org/stix#uses", "http://example.org/stix#ApplicationorSystemExploitation", "head"),
    ],
    "detection": [
        ("http://example.org/stix#OSExhaustionFlood", "http://example.org/stix#description", "Adversaries may perform Endpoint Denial of Service (DoS) attacks to degrade or block the availability of services to users. Endpoint DoS can be performed by exhausting the system resources those services are hosted on or exploiting the system to cause a persistent crash condition. Example services include websites, email services, DNS, and web-based applications.", "tail"),
        ("http://example.org/stix#ServiceExhaustionFlood", "http://example.org/stix#description", "Adversaries may target the different network services provided by systems to conduct a denial of service (DoS). Adversaries often target the availability of DNS and web services, however others have been targeted as well.", "tail"),
        ("http://example.org/stix#NetworkTrafficFlow", "http://example.org/stix#detects", "http://example.org/stix#ApplicationorSystemExploitation", "head"),
        ("http://example.org/stix#NetworkTrafficContent", "http://example.org/stix#detects", "http://example.org/stix#ApplicationorSystemExploitation", "head"),
        ("http://example.org/stix#ApplicationLogContent", "http://example.org/stix#detects", "http://example.org/stix#ApplicationorSystemExploitation", "head"),
        ("http://example.org/stix#HostStatus", "http://example.org/stix#detects", "http://example.org/stix#ApplicationorSystemExploitation", "head")
    ],
    "mitigation": [
        ("http://example.org/stix#FilterNetworkTraffic", "http://example.org/stix#mitigates", "http://example.org/stix#OSExhaustionFlood", "head"),
        ("http://example.org/stix#FilterNetworkTraffic", "http://example.org/stix#mitigates", "http://example.org/stix#ApplicationorSystemExploitation", "head"),
        ("http://example.org/stix#FilterNetworkTraffic", "http://example.org/stix#mitigates", "http://example.org/stix#DirectNetworkFlood", "head"),

    ]

}


def evaluate_triples(group_name, test_triples):
    total_hits = {1: 0, 3: 0, 10: 0}
    total_mrr = 0
    num_predictions = 0
    results = []

    def format_entity(uri):
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

    def compute_metrics(ranks, entity_type, label):
        nonlocal total_hits, total_mrr, num_predictions
        if len(ranks) == 0:
            return
        rank = ranks[0] + 1
        for k in total_hits:
            total_hits[k] += int(rank <= k)
        total_mrr += 1 / rank
        num_predictions += 1
        results.append(f"[{entity_type} Prediction] - {format_entity(label)}\n")
        results.append(f"  Rank: {rank}\n")
        results.append(f"  Hits@1: {int(rank <= 1)}, Hits@3: {int(rank <= 3)}, Hits@10: {int(rank <= 10)}\n")
        results.append(f"  MRR: {1 / rank:.6f}\n")

    for head_label, relation_label, tail_label, prediction_type in test_triples:
        h, r, t = entity_to_id.get(head_label), relation_to_id.get(relation_label), entity_to_id.get(tail_label)
        if None in (h, r, t):
            continue

        results.append(f"{format_entity(head_label)} -[{format_entity(relation_label)}]-> {format_entity(tail_label)}\n")

        if prediction_type in ("tail", "both"):
            predictions_tail = predict_target(model, relation=relation_label, head=head_label, triples_factory=triples_factory).df
            ranks_tail = (predictions_tail["tail_label"] == tail_label).to_numpy().nonzero()[0]
            compute_metrics(ranks_tail, "Tail", tail_label)

        if prediction_type in ("head", "both"):
            predictions_head = predict_target(model, relation=relation_label, tail=tail_label, triples_factory=triples_factory).df
            ranks_head = (predictions_head["head_label"] == head_label).to_numpy().nonzero()[0]
            compute_metrics(ranks_head, "Head", head_label)

        results.append("\n")

    if num_predictions > 0:
        avg_hits = {k: total_hits[k] / num_predictions for k in total_hits}
        avg_mrr = total_mrr / num_predictions
        results.append("Total metrics:\n")
        results.append(f"  Hits@1: {avg_hits[1]:.4f}, Hits@3: {avg_hits[3]:.4f}, Hits@10: {avg_hits[10]:.4f}\n")
        results.append(f"  MRR: {avg_mrr:.6f}\n")

    output_path = os.path.join(output_dir, f"results_{group_name}.txt")
    with open(output_path, "w") as f:
        f.writelines(results)

output_dir = "triple_evaluation"
os.makedirs(output_dir, exist_ok=True)

evaluate_triples("network_structure", test_groups["network_structure"])
print("Network Structure test results saved to triple_evaluation/results_network_structure.txt")

evaluate_triples("description", test_groups["description"])
print("Description test results saved to triple_evaluation/results_description.txt")

evaluate_triples("detection", test_groups["detection"])
print("Detection test results saved to triple_evaluation/results_detection.txt")

evaluate_triples("mitigation", test_groups["mitigation"])
print("Mitigation test results saved to triple_evaluation/results_mitigation.txt")

