CREATE TABLE urls (
  id serial primary key,
  url text not null,
  hash text not null,
  newurl text not null
);
