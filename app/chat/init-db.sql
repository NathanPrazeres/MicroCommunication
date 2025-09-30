-- ==========================================
-- Chat App Database Schema
-- Database: chat_service
-- ==========================================
CREATE DATABASE chat_service;
\connect chat_service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- CHAT TABLES
-- ==========================================

-- Chat rooms/conversations
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100),  -- NULL for direct messages
    description TEXT,
    room_type VARCHAR(20) NOT NULL,  -- 'direct', 'group', 'channel'
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_room_type CHECK (room_type IN ('direct', 'group', 'channel'))
);

CREATE INDEX IF NOT EXISTS idx_rooms_type ON rooms(room_type);
CREATE INDEX IF NOT EXISTS idx_rooms_created_by ON rooms(created_by);

-- Room participants
CREATE TABLE IF NOT EXISTS room_participants (
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    user_id UUID,
    role VARCHAR(20) DEFAULT 'member',  -- 'owner', 'admin', 'member'
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_read_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (room_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member'))
);

CREATE INDEX IF NOT EXISTS idx_room_participants_user_id ON room_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_room_participants_room_id ON room_participants(room_id);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    sender_id UUID,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    reply_to_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_message_type CHECK (message_type IN ('text', 'image', 'file', 'system')),
    CONSTRAINT content_not_empty CHECK (char_length(content) > 0)
);

CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- Message read receipts
CREATE TABLE IF NOT EXISTS message_reads (
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (message_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_message_reads_user_id ON message_reads(user_id);

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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_rooms_updated_at ON rooms;
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();