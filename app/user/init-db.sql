-- ==========================================
-- Chat App Database Schema
-- Database: user_service
-- Used by: User Service
-- ==========================================

-- Create separate database for user service
CREATE DATABASE user_service;

\c user_service;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ==========================================
-- USER PROFILE TABLES
-- ==========================================

-- User profiles - extended user information
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bio TEXT,
    avatar_url VARCHAR(500),
    phone_number VARCHAR(20),
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT first_name_length CHECK (char_length(first_name) >= 1),
    CONSTRAINT last_name_length CHECK (char_length(last_name) >= 1)
);

CREATE INDEX idx_user_profiles_username ON user_profiles(username);

-- User preferences - good for UX/UI
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    read_receipts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    online_status_visible BOOLEAN NOT NULL DEFAULT TRUE,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Contacts/Friends - user relationships
CREATE TABLE user_contacts (
    user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    contact_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    nickname VARCHAR(100),  -- Optional custom name for contact
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (user_id, contact_id),
    CONSTRAINT no_self_contact CHECK (user_id != contact_id)
);

CREATE INDEX idx_contacts_user_id ON user_contacts(user_id);
CREATE INDEX idx_contacts_contact_id ON user_contacts(contact_id);


-- ==========================================
-- FUNCTIONS & TRIGGERS
-- ==========================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create user_profile when user is created
CREATE OR REPLACE FUNCTION create_user_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_preferences (user_id)
    VALUES (NEW.id);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER auto_create_user_preferences AFTER INSERT ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION create_user_preferences();


CREATE ROLE app WITH LOGIN PASSWORD 'keycloak_password';

GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO app;
GRANT ALL ON SCHEMA public TO keycloak;
GRANT ALL ON SCHEMA public TO app;

ALTER DATABASE keycloak OWNER TO keycloak;