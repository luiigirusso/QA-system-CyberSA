FROM python:3.10-slim

ARG BUILD_DATE

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


LABEL maintainer="Luigi, Russo (luiigirusso)"
LABEL description="Docker Image for query translation"
LABEL org.opencontainers.image.name=query_translator
LABEL org.opencontainers.image.title=query_translator
LABEL org.opencontainers.image.created=$BUILD_DATE

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
