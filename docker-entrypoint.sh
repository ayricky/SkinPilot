#!/bin/bash
set -e

# Perform any other necessary setup or configuration

# Check if the database is already populated (optional)
if [ ! -f /var/lib/postgresql/data/populated ]; then
    # Populate the database from the SQL dump file
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f db_utils/dump.sql

    # Create a marker file to indicate that the database is populated
    touch /var/lib/postgresql/data/populated
fi

# Start the PostgreSQL service
exec "$@"
