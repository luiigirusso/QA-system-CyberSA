import os
import re
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

# Initialize FastAPI app
app = FastAPI()

# Pydantic model for request body
class QueryRequest(BaseModel):
    """
    Request model representing a user's natural language question.
    """
    question: str

def extract_name(url: str) -> str:
    """
    Extracts the final segment of a URI by removing known namespace prefixes.

    Args:
        url (str): A full URI string.

    Returns:
        str: The simplified name extracted from the URI.
    """
    prefixes = [
        "http://d3fend.mitre.org/ontologies/d3fend.owl#",
        "http://www.w3.org/2000/01/rdf-schema#",
        "http://example.org/entities/",
        "http://example.org/d3f/",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/2002/07/owl#",
        "http://www.w3.org/2004/02/skos/core#",
        "http://example.org/network#",
        "http://example.org/stix#"
    ]
    # Return the last segment after removing matching prefixes
    return next((re.split(r'[#/]', url)[-1] for prefix in prefixes if url.startswith(prefix)), url)

# Initialize the OpenAI LLM for Cypher translation
llm = ChatOpenAI(
    temperature=0,  # Low temperature for deterministic results
    api_key=os.getenv("OPENAI_API_TOKEN"),
    model="gpt-4o-mini" # Lightweight GPT-4 variant
)

@app.post("/translate")
async def translate_query(request: QueryRequest):
    """
    Endpoint that receives a natural language question and returns a Cypher query.

    Args:
        request (QueryRequest): JSON payload containing the question.

    Returns:
        dict: A dictionary with the translated Cypher query.
    """
    question = request.question

    # Prompt template with system instructions and schema/examples
    prompt = [
        {"role": "system", "content": """
        You are an AI that translates natural language queries into Cypher queries.  
        Your task is to output only the Cypher query with no additional text.  
        The Cypher query must return triples in subject-predicate-object format or the URIs of the entities involved. When representing subject, predicate and object, represent them with s, p, o, respectively.

        ### Graph Schema
        The knowledge graph consists of the following main entity types and relationships:

        **Entities:**
        - `ns0__Network`: Represents a computer network.
        - `Server`: A computing entity providing services, including:
        - `MailServer` (subtypes: `ns1__SMTPServer`, `ns1__IMAPServer`, `ns1__POP3Server`)
        - `ns0__DNSServer`
        - `ns0__VPNServer`
        - `ComputerNetworkNode`: Includes `ns0__Router`, `ns0__WirelessAccessPoint`, `ns0__Firewall`
        - `PersonalComputer`: Includes `ns0__LaptopComputer`, `ns0__DesktopComputer`, `ns0__MobilePhone`
        - `ns2__AttackPattern`: Represents different types of cyber attacks.
        - `ns2__CourseOfAction`: Represents mitigation strategies.
        - `ns2__DataComponent`: Represents detection mechanisms.
        - `ns2__Malware`: Represents different types of malicious software.
        - `ns2__IntrusionSet`: Represents adversarial groups.

        **Relationships:**
        - `ns1__contains`: `(ns0__Network) -[:ns1__contains]-> (Server | ComputerNetworkNode | PersonalComputer)`
        - `ns1__wired_connection`: `(ns1__SMTPServer | ns1__POP3Server | ns0__DNSServer | ns0__VPNServer) -[:ns1__wired_connection]-> (ns0__Router)`
        - `ns1__wireless_connection`: `(ns0__LaptopComputer | ns0__DesktopComputer | ns0__MobilePhone) -[:ns1__wireless_connection]-> (ns0__WirelessAccessPoint)`
        - `ns1__provides_vpn_access`: `(ns0__VPNServer) -[:ns1__provides_vpn_access]-> (DigitalArtifact)`
        - `ns1__delivers_mail`: `(SMTPServer) -[:ns1__delivers_mail]-> (MailServerReceiver)`
        - `ns1__resolves_mail`: `(DNSServer) -[:ns1__resolves_mail]-> (MailServer)`
        - `ns1__validates_mail_domains`: `(DNSServer) -[:ns1__validates_mail_domains]-> (MailServer)`
        - `ns1__filter_traffic`: `(Firewall) -[:ns1__filter_traffic]-> (Server | Router)`
        - `ns2__mitigates`: `(ns2__CourseOfAction) -[:ns2__mitigates]-> (ns2__AttackPattern)`
        - `ns2__detects`: `(ns2__DataComponent) -[:ns2__detects]-> (ns2__AttackPattern)`
        - `ns2__uses`: `(ns2__Malware | ns2__IntrusionSet) -[:ns2__uses]-> (ns2__AttackPattern)`

        ### Examples:

        #### Example 1
        **Natural language:** "Are there DNS, NTP, or other UDP-based services in LAN1?"  
        **Cypher Query:**
        MATCH (s:ns0__Network {rdfs__label: "LAN 1"})-[p:ns1__contains]->(o)
        WHERE tolower(o.uri) CONTAINS "dns" OR tolower(o.uri) CONTAINS "ntp"
        RETURN s.uri AS subject, type(p) AS predicate, o.uri AS object

        #### Example 2
        **Natural language:** "Can you explain how a Reflection Amplification attack works?"
        **Cypher Query:**
        MATCH (ap:ns2__AttackPattern)
        WHERE tolower(ap.uri) CONTAINS "reflectionamplification" 
        RETURN ap.uri AS uri

        #### Example 3
        **Natural language:** "I detected many incoming UDP packets to my network that have 'ANY' as an argument. What might this be due to?"
        **Cypher Query:**
        MATCH (dc:ns2__DataComponent)
        RETURN dc.uri AS uri
        UNION
        MATCH (ap:ns2__AttackPattern)
        RETURN ap.uri AS uri
        
        #### Example 4
        **Natural language:** "How can I mitigate a Reflection Amplification attack?"
        **Cypher Query:**
        MATCH (s)-[p:`ns2__mitigates`]->(o:ns2__AttackPattern)
        WHERE tolower(o.uri) CONTAINS "reflectionamplification"
        RETURN s.uri AS uri

        Ensure that the output strictly follows the Cypher query format and does not include any explanatory text.
        """},
        {"role": "user", "content": f"Question:\n{question}"}
    ]

    # Invoke the language model with the crafted prompt
    response = llm.invoke(prompt)
    cypher_query = response.content.strip()

    return {"cypher_query": cypher_query}
