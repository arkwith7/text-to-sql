# Backend API Documentation

This document outlines the API endpoints for the Smart Business Analytics Assistant backend.

## Base URL

`/api/v1`

---

## Authentication (`/auth`)

Handles user registration, login, token management, and user information retrieval.

| Method | Endpoint             | Description                                  | Authentication |
|--------|----------------------|----------------------------------------------|----------------|
| `POST` | `/register`          | Registers a new user and returns tokens.     | None           |
| `POST` | `/login`             | Authenticates a user and returns tokens.     | None           |
| `POST` | `/refresh`           | Refreshes an access token using a refresh token. | None           |
| `POST` | `/logout`            | Logs out a user by invalidating the refresh token. | JWT Required   |
| `GET`  | `/me`                | Retrieves the current authenticated user's info. | JWT Required   |
| `GET`  | `/stats`             | Retrieves usage statistics for the current user. | JWT Required   |

---

## Query & Schema

Handles natural language queries, SQL execution, and database schema retrieval.

| Method | Endpoint               | Description                                  | Authentication |
|--------|------------------------|----------------------------------------------|----------------|
| `POST` | `/query`               | Processes a natural language query to SQL and executes it. | JWT Required   |
| `GET`  | `/schema`              | Retrieves the database schema information.   | JWT Required   |
| `GET`  | `/queries/popular`     | Gets a list of the most popular queries.     | JWT Required   |
| `POST` | `/queries/suggestions` | Gets AI-powered query suggestions (placeholder). | JWT Required   |

---

## Chat & Streaming (`/chat`)

Manages chat sessions, conversation history, and real-time streaming updates.

| Method | Endpoint                      | Description                                  | Authentication |
|--------|-------------------------------|----------------------------------------------|----------------|
| `POST` | `/stream-query`               | Executes a query with real-time SSE updates. | JWT Required   |
| `POST` | `/sessions`                   | Creates a new chat session.                  | JWT Required   |
| `GET`  | `/sessions`                   | Retrieves all chat sessions for the current user. | JWT Required   |
| `POST` | `/sessions/{session_id}/messages` | Adds a new message to a chat session.        | JWT Required   |
| `GET`  | `/sessions/{session_id}/messages` | Retrieves all messages for a specific chat session. | JWT Required   |
| `DELETE`| `/sessions/{session_id}`      | Deactivates a chat session (soft delete).      | JWT Required   |
| `GET`  | `/sessions/{session_id}/context`| Retrieves chat history formatted for AI context. | JWT Required   |
| `GET`  | `/stream-session/{session_id}`| Streams real-time updates for a session (e.g., for collaboration). | JWT Required |

---

## Analytics

Provides access to user and system-level analytics.

| Method | Endpoint      | Description                          | Authentication |
|--------|---------------|--------------------------------------|----------------|
| `GET`  | `/analytics`  | Retrieves user and system analytics. | JWT Required   |

---

## Admin (`/admin`)

Administrative endpoints for managing the application.

| Method | Endpoint                     | Description                                | Authentication |
|--------|------------------------------|--------------------------------------------|----------------|
| `DELETE`| `/cache`                     | Clears the Redis cache (all or by pattern). | Admin Required |
| `GET`  | `/cache/stats`               | Retrieves statistics about the Redis cache. | Admin Required |
| `GET`  | `/users`                     | Lists all users in the system (placeholder). | Admin Required |
| `POST` | `/users/{user_id}/deactivate`| Deactivates a specific user (placeholder). | Admin Required |

---

## System

General system-level endpoints.

| Method | Endpoint   | Description                                  | Authentication |
|--------|------------|----------------------------------------------|----------------|
| `GET`  | `/health`  | Health check endpoint for monitoring.        | None           | 