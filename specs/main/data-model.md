# Data Model: Todo AI Chatbot

## Overview
This document defines the data models for the Todo AI Chatbot application, including entities, relationships, and validation rules.

## Entity: Task
**Description**: Represents a user's todo item

**Fields**:
- id: UUID (primary key, auto-generated)
- title: String (required, max length 255)
- description: String (optional, max length 1000)
- status: Enum (pending, completed, default: pending)
- user_id: UUID (foreign key to User, required)
- created_at: DateTime (auto-generated)
- updated_at: DateTime (auto-generated, updates on change)

**Validation Rules**:
- Title must not be empty
- Status must be one of the allowed values
- User_id must reference an existing user

## Entity: User
**Description**: Represents a system user

**Fields**:
- id: UUID (primary key, auto-generated)
- username: String (required, unique, max length 100)
- email: String (required, unique, valid email format)
- hashed_password: String (required, for authentication)
- created_at: DateTime (auto-generated)
- updated_at: DateTime (auto-generated, updates on change)

**Validation Rules**:
- Username must be unique and not empty
- Email must be unique and valid format
- Password must meet security requirements

## Entity: Conversation
**Description**: Represents a conversation thread between user and AI

**Fields**:
- id: UUID (primary key, auto-generated)
- user_id: UUID (foreign key to User, required)
- title: String (auto-generated from first message or user-provided)
- created_at: DateTime (auto-generated)
- updated_at: DateTime (auto-generated, updates on change)

**Validation Rules**:
- User_id must reference an existing user

## Entity: Message
**Description**: Represents a message in a conversation

**Fields**:
- id: UUID (primary key, auto-generated)
- conversation_id: UUID (foreign key to Conversation, required)
- role: Enum (user, assistant, required)
- content: String (required, max length 10000)
- timestamp: DateTime (auto-generated)

**Validation Rules**:
- Conversation_id must reference an existing conversation
- Role must be one of the allowed values
- Content must not be empty

## Relationships
- User (1) → Task (Many): A user can have many tasks
- User (1) → Conversation (Many): A user can have many conversations
- Conversation (1) → Message (Many): A conversation can have many messages

## State Transitions
- Task: pending → completed (when marked as done)
- Message: immutable after creation (no state changes)
- Conversation: active (no explicit state changes, remains active)

## Indexes
- Task: index on user_id for efficient user task retrieval
- Message: index on conversation_id for efficient conversation message retrieval
- User: indexes on username and email for authentication efficiency