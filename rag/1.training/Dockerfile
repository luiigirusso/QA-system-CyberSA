FROM python:3.10-slim

ARG BUILD_DATE

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

LABEL maintainer="Luigi, Russo (luiigirusso)"
LABEL description="Docker Image for training TransE KGE"
LABEL org.opencontainers.image.name=training
LABEL org.opencontainers.image.title=training
LABEL org.opencontainers.image.created=$BUILD_DATE

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY __main__.py /opt/
WORKDIR /opt/

CMD ["python", "__main__.py"]
