FROM frolvlad/alpine-miniconda3
MAINTAINER pasit.dev

RUN apk add --no-cache wget curl vim \
    && rm -rf /var/cache/apk/* \
    && pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
    && mkdir -p /usr/src/app \
    && rm -rf /root/.cache
WORKDIR /usr/src/app
CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=3000"]