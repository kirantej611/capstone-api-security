#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE victim_ecommerce_db;
    GRANT ALL PRIVILEGES ON DATABASE victim_ecommerce_db TO admin;
EOSQL
