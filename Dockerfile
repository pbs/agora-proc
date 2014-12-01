FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN easy_install --upgrade pip
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install --editable .
RUN pip install -r ./requirements/dev.txt
