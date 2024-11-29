FROM python:3.12-alpine

ENV BUILD=/app

RUN mkdir -p $BUILD

COPY requirements_docker.txt $BUILD
COPY scripts/download-books.py $BUILD

WORKDIR $BUILD

RUN pip install -r requirements_docker.txt

CMD ["sh"]