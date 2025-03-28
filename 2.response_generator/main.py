from fastapi import FastAPI
from pydantic import BaseModel
import os
from langchain_openai import ChatOpenAI


app = FastAPI()

# Modello dati per la richiesta
class ResponseRequest(BaseModel):
    question: str
    context: str

llm = ChatOpenAI(
    temperature=0,
    api_key=os.getenv("OPENAI_API_TOKEN"),
    model_name="gpt-4o-mini"
)

@app.post("/generate")
async def generate_response(request: ResponseRequest):
    prompt = [
    (
        "system",
        """
        You are an AI assistant designed to support a security analyst in monitoring, detecting, and mitigating DDoS and DoS attacks.  
        Your primary goal is to enhance the analyst's cyber situation awareness by providing concise, context-aware insights.  

        # Instructions  
        - Answer exclusively based on the information provided in the context; do not use your own pre-existing knowledge or external sources. 
        - Prioritize clear and concise answers that directly assist the analyst.  
        - Focus on practical insights that improve the analyst’s decision-making.  
        """,
    ),
    ("human", f"Context: {request.context}\n\nQuestion: {request.question}"),
    ]

    response = llm.invoke(prompt)
    return {"answer": response.content}
