# pfurl.me

[![Build Status](https://travis-ci.org/PacketFire/pfurl.me.svg?branch=master)](https://travis-ci.org/PacketFire/pfurl.me)

## Description
Pfurl is a url shortening API designed to be easily used with ``curl``. A user interface is also included via ``/up`` route for ease of use if ``curl`` is not an option.

## Dependencies
* Docker + Compose
* Python 3.6+

## Building
```shell
$ git clone https://github.com/PacketFire/pfurl.me
$ cd pfurl.me ; make setup ; make pip-install
```

Initialize Docker containers which will install Postgres and Flyway DB
```shell
$ docker-compose up postgres
$ docker-compose run flyway-migrate
```

## API Usage
The api can be called via the ``curl`` command, if executed correctly a shortened url will be returned.

Example: ``curl -X POST -d '{"url": "http://yourlongurlhere.com"}' -H 'Content-Type: application/json' pfurl.me``
