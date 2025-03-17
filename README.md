# AI Hive Task Management System

A task management system built with Domain-Driven Design principles, designed to orchestrate AI-driven workflows.

## Project Structure

The project follows a clean architecture with Domain-Driven Design (DDD) principles:

```
src/
├── core/                      # Core domain components
│   ├── domain_events/         # Domain events
│   └── message_broker/        # Message broker interface and implementations
├── task_management/           # Task management bounded context
│   ├── api/                   # API controllers
│   ├── application/           # Application services
│   ├── domain/                # Domain model
│   │   ├── entities/          # Domain entities
│   │   ├── events/            # Domain events
│   │   ├── repositories/      # Repository interfaces
│   │   └── value_objects/     # Value objects
│   └── infrastructure/        # Infrastructure implementations
│       └── repositories/      # Repository implementations
├── orchestration/             # Orchestration bounded context
│   └── domain/                # Orchestration domain model
├── config.py                  # Application configuration
├── dependencies.py            # Dependency injection
└── main.py                    # Application entry point
```

## Features

- Task creation, assignment, and management
- Status transitions with validation
- Event-driven architecture
- Asynchronous task orchestration
- RESTful API

## Domain Model

### Task Entity

The core entity in the system is the `Task`, which represents a unit of work. Tasks have the following properties:

- ID, title, description
- Status (CREATED, ASSIGNED, IN_PROGRESS, BLOCKED, REVIEW, COMPLETED, CANCELED)
- Priority (LOW, MEDIUM, HIGH, CRITICAL)
- Assignee, creator
- Due date, timestamps
- Parent task, requirements
- Tags, artifacts

### Domain Events

The system uses domain events to communicate state changes:

- TaskCreatedEvent
- TaskAssignedEvent
- TaskStatusChangedEvent
- TaskCompletedEvent
- TaskCanceledEvent

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- RabbitMQ

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/aihive.git
   cd aihive
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables or use defaults:
   ```
   export MONGODB_URI=mongodb://localhost:27017
   export RABBITMQ_URI=amqp://guest:guest@localhost:5672/
   ```

5. Run the application:
   ```
   python -m src.main
   ```

6. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Testing

Run the tests with pytest:

```
pytest
```

## API Endpoints

- `POST /tasks` - Create a new task
- `GET /tasks` - List tasks with optional filters
- `GET /tasks/{task_id}` - Get a specific task
- `PUT /tasks/{task_id}/status` - Update task status
- `PUT /tasks/{task_id}/assign` - Assign a task
- `PUT /tasks/{task_id}/complete` - Complete a task
- `PUT /tasks/{task_id}/cancel` - Cancel a task

## License

This project is licensed under the MIT License - see the LICENSE file for details. 