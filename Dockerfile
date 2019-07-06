FROM python:3.6-alpine

COPY  config.yaml fpinger.py requirements.txt  /run/
RUN  pip install -r /run/requirements.txt && \
     apk update && apk add fping

CMD [ "python", "/run/fpinger.py", "--config", "/run/config.yaml" ]


