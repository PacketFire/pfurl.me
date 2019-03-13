CREATE TABLE urls (
  id serial primary key,
  hash text not null,
  url text not null,
  newurl text not null
);
