from fastapi import FastAPI
from pydantic import BaseModel
import os
from langchain_openai import ChatOpenAI

# Initialize the FastAPI app
app = FastAPI()

# Define the request payload model
class ResponseRequest(BaseModel):
    """
    Request model containing the user's question and the associated context.
    """
    question: str
    context: str

# Initialize the OpenAI language model
llm = ChatOpenAI(
    temperature=0,  # Deterministic output for reproducible results
    api_key=os.getenv("OPENAI_API_TOKEN"), # Load API key from environment
    model="gpt-4o-mini" # Use a lightweight GPT-4 variant
)

@app.post("/generate")
async def generate_response(request: ResponseRequest):
    """
    Endpoint that generates a context-aware answer to a cybersecurity-related question.

    This endpoint is designed to assist cybersecurity analysts in monitoring, 
    detecting, and mitigating DDoS and DoS attacks by providing relevant insights 
    based solely on a given context.

    Args:
        request (ResponseRequest): JSON payload containing both the question and the context.

    Returns:
        dict: A dictionary with a single key "answer" containing the model's response.
    """
    
    # Define the prompt used to guide the language model's behavior
    prompt = [
        {"role": "system", "content": """
        You are an AI assistant designed to support a security analyst in monitoring, detecting, and mitigating DDoS and DoS attacks.  
        Your primary goal is to enhance the analyst's cyber situation awareness by providing concise, context-aware insights.  

        # Instructions  
        - Answer exclusively based on the information provided in the context; do not use your own pre-existing knowledge or external sources. 
        - Prioritize clear and concise answers that directly assist the analyst.  
        - Focus on practical insights that improve the analyst’s decision-making. 
        """},
        {"role": "user", "content": f"Context: {request.context}\n\nQuestion: {request.question}"}
    ]

    # Invoke the language model with the crafted prompt
    response = llm.invoke(prompt)

    # Return the cleaned answer
    return {"answer": response.content.strip()}
