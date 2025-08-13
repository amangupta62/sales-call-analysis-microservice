-- Database initialization script for Sales Call Analysis Microservice

-- Create database if it doesn't exist
-- This will be handled by the POSTGRES_DB environment variable

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual tables will be created by SQLAlchemy models
-- This file can be used for any additional database setup or initial data

-- Create indexes for better performance (optional)
-- These can be added after the tables are created by the application

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE sales_calls_db TO user;
GRANT ALL PRIVILEGES ON SCHEMA public TO user;

-- Set timezone
SET timezone = 'UTC';
