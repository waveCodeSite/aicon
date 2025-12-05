-- AICG Platform Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Create extensions if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant privileges to the application user
-- Note: The user is already created by POSTGRES_USER environment variable
-- This script just ensures proper permissions

-- The database and user are automatically created by Docker PostgreSQL image
-- based on POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD environment variables

-- Additional initialization can be added below as needed
