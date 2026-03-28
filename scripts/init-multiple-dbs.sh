#!/bin/bash
# Creates separate databases for each service inside the local Postgres container
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE prism_pos;
  CREATE DATABASE prism_inventory;
  CREATE DATABASE prism_auth;
  GRANT ALL PRIVILEGES ON DATABASE prism_pos       TO $POSTGRES_USER;
  GRANT ALL PRIVILEGES ON DATABASE prism_inventory TO $POSTGRES_USER;
  GRANT ALL PRIVILEGES ON DATABASE prism_auth      TO $POSTGRES_USER;
EOSQL

echo "Databases prism_pos, prism_inventory, prism_auth created."
