# Backend API Documentation

This document outlines the API endpoints for the Smart Business Analytics Assistant backend.

## Base URL

All V1 APIs are prefixed with `/api/v1`.

---

## System

General system-level endpoints.

| Method | Endpoint  | Description                                                             | Authentication |
| ------ | --------- | ----------------------------------------------------------------------- | -------------- |
| `GET`  | `/health` | Health check endpoint for monitoring. Responds with `{"status": "ok"}`. | None           |

---

## Authentication (`/auth`)

Handles user registration, login, and profile management.

| Method | Endpoint             | Description                                                           | Authentication |
| ------ | -------------------- | --------------------------------------------------------------------- | -------------- |
| `POST` | `/register`          | Registers a new user and returns tokens.                              | None           |
| `POST` | `/login`             | Authenticates a user and returns tokens.                              | None           |
| `POST` | `/logout`            | Logs out a user by invalidating their token.                          | JWT Required   |
| `GET`  | `/me`                | Retrieves the current authenticated user's info.                      | JWT Required   |
| `POST` | `/change-password`   | Allows an authenticated user to change their password.                | JWT Required   |
| `GET`  | `/stats`             | Retrieves detailed usage statistics for the current user.             | JWT Required   |
| `GET`  | `/model-stats`       | Retrieves detailed model-specific usage statistics for the user.      | JWT Required   |
| `GET`  | `/token-breakdown`   | Retrieves a breakdown of token usage by different categories.         | JWT Required   |
| `GET`  | `/daily-model-stats` | Retrieves daily model statistics for the user (default last 30 days). | JWT Required   |
| `GET`  | `/admin/stats`       | Retrieves authentication statistics for the whole system.             | Admin Required |

---

## AI Query (`/query`)

Handles natural language to SQL conversion and execution.

| Method   | Endpoint              | Description                                                     | Authentication |
| -------- | --------------------- | --------------------------------------------------------------- | -------------- |
| `POST`   | `/`                   | Processes a natural language query to generate and execute SQL. | JWT Required   |
| `POST`   | `/validate`           | Validates a given SQL query without executing it.               | JWT Required   |
| `GET`    | `/history`            | Retrieves the query history for the current user.               | JWT Required   |
| `DELETE` | `/history/{query_id}` | Deletes a specific query from the user's history.               | JWT Required   |

---

## Schema (`/schema`)

Provides access to database schema information.

| Method | Endpoint               | Description                                                | Authentication |
| ------ | ---------------------- | ---------------------------------------------------------- | -------------- |
| `GET`  | `/`                    | Retrieves comprehensive schema information for a database. | JWT Required   |
| `GET`  | `/tables`              | Retrieves a list of all table names in the database.       | JWT Required   |
| `GET`  | `/tables/{table_name}` | Retrieves detailed information for a specific table.       | JWT Required   |
| `GET`  | `/relationships`       | Retrieves all foreign key relationships in the database.   | JWT Required   |

---

## Chat (`/chat`)

Manages conversational AI sessions.

| Method   | Endpoint                          | Description                                                       | Authentication |
| -------- | --------------------------------- | ----------------------------------------------------------------- | -------------- |
| `POST`   | `/sessions`                       | Creates a new chat session.                                       | JWT Required   |
| `GET`    | `/sessions`                       | Retrieves all chat sessions for the current user.                 | JWT Required   |
| `GET`    | `/sessions/{session_id}`          | Retrieves details for a specific chat session.                    | JWT Required   |
| `DELETE` | `/sessions/{session_id}`          | Deletes a chat session and its history.                           | JWT Required   |
| `POST`   | `/sessions/{session_id}/messages` | Adds a new message to a chat session.                             | JWT Required   |
| `GET`    | `/sessions/{session_id}/messages` | Retrieves all messages for a specific chat session.               | JWT Required   |
| `POST`   | `/sessions/{session_id}/query`    | Processes a natural language query within a chat session context. | JWT Required   |
| `GET`    | `/status`                         | Gets the status of the chat system components.                    | JWT Required   |

---

## Token Usage (`/tokens`)

Provides endpoints for tracking and managing LLM token usage.

| Method | Endpoint            | Description                                                           | Authentication |
| ------ | ------------------- | --------------------------------------------------------------------- | -------------- |
| `GET`  | `/usage`            | Retrieves detailed token usage statistics for the current user.       | JWT Required   |
| `GET`  | `/limits`           | Retrieves the configured token limits and current usage against them. | JWT Required   |
| `GET`  | `/rate-limit-check` | Checks if the user is currently within their rate limits.             | JWT Required   |
| `GET`  | `/dashboard`        | Retrieves a summary of token usage data for a user-facing dashboard.  | JWT Required   |

---

## Analytics (`/analytics`)

Provides access to user and system-level analytics.

| Method | Endpoint              | Description                                                     | Authentication |
| ------ | --------------------- | --------------------------------------------------------------- | -------------- |
| `GET`  | `/usage`              | Retrieves usage analytics for the current user.                 | JWT Required   |
| `GET`  | `/performance`        | Retrieves performance analytics for the current user.           | JWT Required   |
| `GET`  | `/export`             | Exports user analytics data in a specified format (e.g., JSON). | JWT Required   |
| `GET`  | `/system/usage`       | Retrieves system-wide usage analytics.                          | Admin Required |
| `GET`  | `/system/performance` | Retrieves system-wide performance analytics.                    | Admin Required |

---

## Admin (`/admin`)

Administrative endpoints for managing the application.

| Method   | Endpoint                  | Description                                 | Authentication |
| -------- | ------------------------- | ------------------------------------------- | -------------- |
| `GET`    | `/users`                  | Lists all users in the system.              | Admin Required |
| `PUT`    | `/users/{user_id}/role`   | Updates the role for a specific user.       | Admin Required |
| `PUT`    | `/users/{user_id}/status` | Activates or deactivates a specific user.   | Admin Required |
| `DELETE` | `/users/{user_id}`        | Deletes a user from the system.             | Admin Required |
| `GET`    | `/system/status`          | Retrieves the overall status of the system. | Admin Required |
| `POST`   | `/system/cache/clear`     | Clears the application's Redis cache.       | Admin Required |
| `GET`    | `/logs`                   | Retrieves system logs (placeholder).        | Admin Required |

 