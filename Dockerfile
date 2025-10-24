FROM python:3.14-alpine

LABEL maintainer="contato@henriquesebastiao.com"
LABEL version="0.1.2"
LABEL description="CLI client for the Confy encrypted communication system"

RUN apk update && \
    apk add --no-cache bash && \
    pip install --no-cache-dir confy-cli==0.1.2

CMD [ "bash" ]