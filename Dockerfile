FROM python:3.12-alpine

ENV BUILD=/app

RUN mkdir -p $BUILD

COPY requirements_docker.txt $BUILD
COPY scripts/1-preprocess/1-download-books.py $BUILD
COPY scripts/1-preprocess/3-sample-pages.py $BUILD

WORKDIR $BUILD

RUN pip install -r requirements_docker.txt

CMD ["sh"]
