# AI Hive Task Management System

A task management system built with Domain-Driven Design principles, designed to orchestrate AI-driven workflows.

## Project Structure

The project follows a clean architecture with Domain-Driven Design (DDD) principles:

```
src/
├── core/                      # Core domain components
│   ├── domain_events/         # Domain events
│   ├── message_broker/        # Message broker interface and implementations
│   └── agent/                 # Agent interfaces and implementations
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
├── product_definition/        # Product definition bounded context
│   ├── agents/                # Product Manager Agent and related tools
│   ├── domain/                # Domain model for product requirements
│   ├── application/           # Application services including task polling
│   └── infrastructure/        # Infrastructure implementations
│       └── repositories/      # Repository implementations
├── orchestration/             # Orchestration bounded context
│   ├── application/           # Application services including task scanning
│   └── domain/                # Domain model for orchestration
├── infrastructure/            # Shared infrastructure components
│   ├── message_queue/         # Message queue and event handling
│   └── persistence/           # Shared persistence utilities
├── config.py                  # Application configuration
├── dependencies.py            # Dependency injection
├── workflow_integration.py    # Workflow integration service
└── main.py                    # Application entry point
```

## Features

- Task creation, assignment, and management
- Status transitions with validation
- Event-driven architecture
- Asynchronous task orchestration
- RESTful API
- AI-powered agents for task processing
- Workflow integration between bounded contexts

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

## AI-Powered Agents

AIHive includes AI-powered agents that utilize Large Language Models (LLMs) to perform intelligent tasks:

### Available Agents

1. **Product Manager Agent**: Analyzes product requirements, generates clarification questions, and creates comprehensive PRD documents.
2. **Orchestrator Agent**: Coordinates between multiple specialized agents, distributing tasks based on agent capabilities.

### Agent Architecture

- Base `AIAgent` class that handles common LLM operations
- LangChain integration for structured LLM interactions
- Tool integration framework for extensibility
- Error handling with fallback mechanisms

### Configuration

The AI agents require OpenAI API access. Set the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_DEFAULT_MODEL=gpt-4-turbo-preview  # or another compatible model
OPENAI_TEMPERATURE=0.7  # adjust for more/less creative responses
```

### Adding New AI Agents

To create a new AI-powered agent:

1. Extend the `AIAgent` base class in `src/core/agent/ai_agent.py`
2. Implement the required methods, especially `_setup_prompt()` to define the agent's system prompt
3. Register your agent in the dependency injection system in `src/dependencies.py`

## Workflow Integration

The system implements an asynchronous workflow integration between bounded contexts using an event-driven architecture. This enables the orchestration of complex workflows across the system.

For detailed information, see [Workflow Integration Documentation](docs/workflow_integration.md).

### Key Components

- **Message Queue**: Central communication mechanism supporting publishing and subscribing to events and commands
- **Domain Events and Commands**: Strongly typed messages with metadata
- **Task Scanning Service**: Periodically scans for tasks that need attention
- **Task Polling Service**: Polls for tasks assigned to agent pools and delegates processing
- **Error Handling**: Retry mechanisms, dead letter queues, and comprehensive error logging
- **Event Monitoring**: Tracking of events, detection of stalled workflows, and alerting

### Message Broker Options

The system supports multiple message broker implementations:

1. **RabbitMQ Broker (Default for Production)**
   - Robust message broker for distributed systems
   - Supports message persistence, high availability, and clustering
   - Requires a RabbitMQ server

2. **In-Memory Broker**
   - Simple in-memory implementation for development and testing
   - No external dependencies required
   - Allows running multiple agents within a single process
   - Not suitable for production or distributed deployments

To configure the message broker type, set one of the following:

```bash
# In .env file
MESSAGE_BROKER_TYPE=rabbitmq  # or "in_memory"
RABBITMQ_CONNECTION_URI=amqp://guest:guest@localhost:5672/  # For RabbitMQ
```

Or via YAML configuration:

```yaml
message_broker:
  type: rabbitmq  # or "in_memory"
  connection_uri: amqp://guest:guest@localhost:5672/  # For RabbitMQ
```

### Usage

To start the workflow integration service:

```bash
# Using in-memory message queue (for development)
python src/workflow_integration.py

# Using RabbitMQ (for production)
RABBITMQ_HOST=rabbitmq-server RABBITMQ_USERNAME=admin RABBITMQ_PASSWORD=password \
python src/workflow_integration.py --message-queue-type rabbitmq
```

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- RabbitMQ
- OpenAI API key (for AI agents)

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
   export OPENAI_API_KEY=your_openai_api_key  # Required for AI agents
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

## Storage Options

### Product Requirements Storage

The system provides multiple storage options for product requirements:

1. **MongoDB Storage (Default)**
   - Robust document database for production use
   - Supports efficient querying and indexing
   - Requires MongoDB server

2. **File-based Storage**
   - Simple JSON file-based storage
   - Each requirement stored as a separate JSON file
   - No database server required
   - Good for development and simpler deployments

To configure the storage type, set one of the following:

```bash
# In .env file
PRODUCT_REQUIREMENT_STORAGE_TYPE=mongodb  # or "file"
PRODUCT_REQUIREMENT_FILE_STORAGE_DIR=data/product_requirements  # For file-based storage
```

Or via YAML configuration:

```yaml
product_definition:
  storage_type: mongodb  # or "file"
  file_storage_dir: data/product_requirements  # For file-based storage
```

## Architecture Documentation

For more details about the system architecture, see:
- [Architecture Overview](docs/arch/architecture_overview.md)
- [Component Architecture](docs/arch/component_architecture.md)
- [Data Flow Architecture](docs/arch/data_flow_architecture.md)
- [Technology Stack](docs/arch/technology_stack.md)
- [Workflow Integration](docs/workflow_integration.md)

## Architecture Decision Records (ADRs)

- [ADR-007: Configurable Message Broker Implementation](docs/arch/adr/007-configurable-message-broker.md)
- [ADR-006: Asynchronous Workflow Integration](docs/arch/adr/006-asynchronous-workflow-integration.md)
- [ADR-005: Product Requirements Storage Mechanism](docs/arch/adr/005-product-requirements-storage.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 