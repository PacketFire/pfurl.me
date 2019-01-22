FROM python:3.7.2-stretch

RUN apt-get update

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "pfurl" ]