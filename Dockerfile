FROM ubuntu:trusty
RUN apt-get install -y wget
RUN apt-get install -y software-properties-common && \
    add-apt-repository ppa:fkrull/deadsnakes && \
    apt-get update && \
    apt-get install -y python2.6 python2.7
RUN cd /tmp; wget https://bootstrap.pypa.io/get-pip.py; \
    python2.7 get-pip.py; rm get-pip.py;
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install --editable .
RUN pip install -r ./requirements/dev.txt
RUN tox
