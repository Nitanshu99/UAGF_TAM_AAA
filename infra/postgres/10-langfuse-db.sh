#!/bin/sh
# Create the dedicated Langfuse role + database on first cluster init.
#
# Langfuse v3+ runs its own Prisma migrations on start-up. Pointing it at the
# application's ${POSTGRES_DB} put those migrations in the same schema Alembic
# owns, so `make up` ran two independent migration systems against one database.
# It also connected as the application superuser; it now gets a role that owns
# only its own database.
#
# Docker's postgres entrypoint executes this only when the data volume is empty.
# For an existing deployment, run the equivalent once by hand (SETUP.md §8).
set -e

LF_DB="${LANGFUSE_POSTGRES_DB:-langfuse}"
LF_USER="${LANGFUSE_POSTGRES_USER:-langfuse}"
LF_PASSWORD="${LANGFUSE_POSTGRES_PASSWORD:-changeme}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${LF_USER}') THEN
            CREATE ROLE "${LF_USER}" LOGIN PASSWORD '${LF_PASSWORD}';
        END IF;
    END
    \$\$;
    SELECT 'CREATE DATABASE "${LF_DB}" OWNER "${LF_USER}"'
    WHERE NOT EXISTS (
        SELECT FROM pg_database WHERE datname = '${LF_DB}'
    )\gexec
EOSQL

echo "langfuse role ${LF_USER} and database ${LF_DB} ready"
