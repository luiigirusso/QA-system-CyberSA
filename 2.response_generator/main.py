from fastapi import FastAPI
from pydantic import BaseModel
import os
from langchain_openai import ChatOpenAI

app = FastAPI()

# Data model for request payload
class ResponseRequest(BaseModel):
    question: str
    context: str

# Initialize OpenAI language model with API key from environment variables
llm = ChatOpenAI(
    temperature=0,  # Set to 0 for deterministic responses
    api_key=os.getenv("OPENAI_API_TOKEN"),
    model="gpt-4o-mini"
)

@app.post("/generate")
async def generate_response(request: ResponseRequest):
    """
    Generates a response based on the given question and context using OpenAI's language model.
    The AI assistant is designed to support cybersecurity analysts in detecting and mitigating
    DDoS and DoS attacks.
    """
    
    # Construct the prompt for the AI assistant
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

    # Invoke OpenAI model to generate response
    response = llm.invoke(prompt)

    # Return the generated answer as JSON response
    return {"answer": response.content.strip()}
