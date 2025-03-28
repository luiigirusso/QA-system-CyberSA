import os
import re
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

app = FastAPI()

# Data model for request payload
class QueryRequest(BaseModel):
    question: str

# Function to extract the name from URIs by removing known prefixes
def extract_name(url: str) -> str:
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
    # Use next() for efficiency; return the last segment after a known prefix if matched
    return next((re.split(r'[#/]', url)[-1] for prefix in prefixes if url.startswith(prefix)), url)

# Initialize connection to OpenAI's language model
llm = ChatOpenAI(
    temperature=0,  # Set temperature to 0 for deterministic responses
    api_key=os.getenv("OPENAI_API_TOKEN"),
    model="gpt-4o-mini"
)

@app.post("/translate")
async def translate_query(request: QueryRequest):
    question = request.question

    # Constructing the prompt for translating NL queries to Cypher
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
        - `DataComponent`: Represents detection mechanisms.
        - `ns2__Malware`: Represents different types of malicious software.
        - `ns2__IntrusionSet`: Represents adversarial groups.

        **Relationships:**
        - `ns1__contains`: `(ns0__Network) -[:ns1__contains]-> (Server | ComputerNetworkNode | PersonalComputer)`
        - `ns1__wired_connection`: `(ns1__SMTPServer | ns1__POP3Server | ns0__DNSServer | ns0__VPNServer) -[:ns1__wired_connection]-> (ns0__Router)`
        - `ns1__wireless_connection`: `(ns0__LaptopComputer | ns0__DesktopComputer | ns0__MobilePhone) -[:ns1__wireless_connection]-> (ns0__WirelessAccessPoint)`
        - `provides_vpn_access`: `(ns0__VPNServer) -[:provides_vpn_access]-> (DigitalArtifact)`
        - `delivers_mail`: `(SMTPServer) -[:delivers_mail]-> (MailServerReceiver)`
        - `resolves_mail`: `(DNSServer) -[:resolves_mail]-> (MailServer)`
        - `validates_mail_domains`: `(DNSServer) -[:validates_mail_domains]-> (MailServer)`
        - `ns1__filter_traffic`: `(Firewall) -[:ns1__filter_traffic]-> (Server | Router)`
        - `mitigates`: `(ns2__CourseOfAction) -[:mitigates]-> (ns2__AttackPattern)`
        - `ns2__detects`: `(DataComponent) -[:ns2__detects]-> (ns2__AttackPattern)`
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
        RETURN DISTINCT dc.uri AS uri
        UNION
        MATCH (ap:ns2__AttackPattern)
        RETURN DISTINCT ap.uri AS uri
        
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

    # Invoke OpenAI model to generate the Cypher query
    response = llm.invoke(prompt)
    cypher_query = response.content.strip()

    # Return the Cypher query as JSON response
    return {"cypher_query": cypher_query}
