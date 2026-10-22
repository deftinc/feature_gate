-- RFC 9562 UUIDv7. PostgreSQL 18 ships uuidv7(), but this supports older
-- servers. Like PostgreSQL 18's, it fills the 12-bit rand_a field with
-- sub-millisecond clock precision so ids sort in creation order.
CREATE FUNCTION feature_gate_uuidv7() RETURNS uuid
LANGUAGE plpgsql VOLATILE AS $$
DECLARE
  epoch_ms numeric := extract(epoch FROM clock_timestamp()) * 1000;
  unix_ms bigint := floor(epoch_ms);
  sub_ms integer := floor((epoch_ms - unix_ms) * 4096);
  -- gen_random_uuid() is a v4 UUID: random bits with the RFC variant already set.
  bytes bytea := uuid_send(gen_random_uuid());
BEGIN
  bytes := overlay(bytes PLACING substring(int8send(unix_ms) FROM 3) FROM 1 FOR 6);
  bytes := set_byte(bytes, 6, (x'70'::integer) | (sub_ms >> 8));
  bytes := set_byte(bytes, 7, sub_ms & 255);
  RETURN encode(bytes, 'hex')::uuid;
END
$$;

CREATE TABLE feature_gate_features (
  id uuid PRIMARY KEY DEFAULT feature_gate_uuidv7(),
  key text NOT NULL UNIQUE,
  name text,
  description text,
  enabled boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
