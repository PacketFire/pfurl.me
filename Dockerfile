FROM packetfire/pfurl:latest

RUN apt-get update

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "pfurl" ]