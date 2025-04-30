FROM python:3.10-slim

ARG BUILD_DATE

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

LABEL maintainer="Luigi, Russo (luiigirusso)"
LABEL description="Docker Image for RAG"
LABEL org.opencontainers.image.name=rag
LABEL org.opencontainers.image.title=rag
LABEL org.opencontainers.image.created=$BUILD_DATE

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY __main__.py /opt/
WORKDIR /opt/

CMD ["streamlit", "run", "/opt/__main__.py", "--server.port=8502", "--server.address=0.0.0.0"]
