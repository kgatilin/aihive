# AI-Driven Development Pipeline

A modular, event-driven system designed to automate and orchestrate the software development lifecycle using AI agents for product refinement and code generation.

## Project Overview

The AI-Driven Development Pipeline creates a structured workflow for transforming raw requirements into production-ready code through a series of AI-assisted stages:

1. Requirements are submitted through a human interface
2. The orchestrator agent manages workflow progression
3. The product agent refines requirements into detailed specifications
4. The coding agent generates code based on the specifications
5. Human validation occurs at key checkpoints for quality control

## Architecture

The system follows Domain-Driven Design principles with a clean, modular architecture:

- **Human Interface Layer** - Accepts requirements and exposes REST API for interaction
- **Task Management System** - Central tracking system for all workflow operations
- **Orchestrator Agent** - Coordinates workflow by assigning tasks to appropriate agents
- **Product Agent** - Refines raw requirements into structured specifications
- **Coding Agent** - Generates code based on specifications

## Key Architectural Principles

- **Event-Driven Communication** - Components interact through domain events
- **Asynchronous Processing** - All operations are non-blocking for scalability
- **Domain Isolation** - Clear boundaries between different parts of the system
- **Human Validation Checkpoints** - Strategic points for human oversight

## Getting Started

### Prerequisites

- Python 3.9+
- RabbitMQ
- MongoDB

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/kgatilin/aihive.git
   cd aihive
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create an `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```

5. Make sure MongoDB and RabbitMQ are running.

### Running the Application

Start the main application:

```
python -m src.app
```

This will start:
- The API server (default: http://localhost:8080)
- The orchestrator agent
- All message broker connections

## Development

### Project Structure

```
src/
├── app.py                     # Main application entry point
├── config.py                  # Configuration management
├── core/                      # Core domain
│   ├── common/                # Shared utilities
│   └── domain_events/         # Domain events
├── task_management/           # Task management context
│   ├── domain/                # Task domain model
│   ├── application/           # Task services
│   └── infrastructure/        # Task repositories
├── orchestration/             # Orchestration context
│   └── domain/                # Orchestrator agents
├── product_definition/        # Product context
│   └── domain/                # Product domain model
├── human_interaction/         # Human interface context
│   └── api/                   # REST API
└── infrastructure/            # Shared infrastructure
```

### Running Tests

Run tests with pytest:

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 