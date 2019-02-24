FROM packetfire/pfurl:latest

RUN apt-get update

COPY . /pfurl.me/

RUN pip install --upgrade pip
RUN cd pfurl.me/ && \
    pip install -r requirements.txt

WORKDIR /pfurl.me
ENTRYPOINT [ "python", "pfurl" ]