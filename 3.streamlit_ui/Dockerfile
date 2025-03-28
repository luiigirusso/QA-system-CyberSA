FROM python:3.10-slim

ARG BUILD_DATE

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


LABEL maintainer="Luigi, Russo (luiigirusso)"
LABEL description="Docker Image for response generation"
LABEL org.opencontainers.image.name=response_generator
LABEL org.opencontainers.image.title=response_generator
LABEL org.opencontainers.image.created=$BUILD_DATE

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
