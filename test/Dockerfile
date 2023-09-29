FROM python:3.10

WORKDIR /

COPY . /tests

WORKDIR /tests
RUN pip install -r requirements.txt

CMD [ "/tests/run_tests.sh" ]
