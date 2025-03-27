FROM python:3.10-slim

ARG BUILD_DATE

RUN apt-get update 
RUN apt-get install -y git

LABEL maintainer="Luigi, Russo (luiigirusso)"
LABEL description="Docker Image for extracting embeddings from TransE KGE"
LABEL org.opencontainers.image.name=embeddings
LABEL org.opencontainers.image.title=embeddings
LABEL org.opencontainers.image.created=$BUILD_DATE

RUN python -m pip install --no-cache --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY __main__.py /opt/

WORKDIR /opt/

ENTRYPOINT ["python", "__main__.py"]