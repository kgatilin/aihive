# AI-Driven Development Pipeline: Component Architecture

## Introduction

This document outlines the key components of the AI-driven development pipeline, focusing on their interfaces and interaction patterns. The architecture is designed to be simple and practical, avoiding unnecessary complexity.

## Core Components

### Human Interface

- **Purpose**: Provides interaction points for humans to input requirements and validate outputs
- **Implementation Options**:
  - Slack integration
  - Web-based dashboard
  - CLI tool
- **Key Functions**:
  - Submit requirements (linking to markdown files in git)
  - Review AI outputs
  - Provide approvals at validation checkpoints
  - Track overall project status

### Task Tracking System

- **Purpose**: Central system for managing the status and progress of all work items
- **Implementation**: Similar to Jira or other issue tracking systems
- **Task Statuses**:
  - Verifying PRD - Initial validation of product requirements
  - Verifying Acceptance Criteria - Ensuring clear success metrics
  - Verifying Architecture - Reviewing the proposed technical approach
  - Verifying Execution Plan - Evaluating the implementation strategy
  - Queued for Development - Ready to be picked up by coding agent
  - In Development - Currently being implemented
  - Code Review - Awaiting human validation
  - Testing - Undergoing automated testing
  - Ready for Deployment - Verified and ready to deploy
  - Deployed - Live in production
- **Key Features**:
  - Git integration for PRD linking (PRDs stored as markdown files)
  - Status tracking with timestamps
  - Assignment functionality
  - Commenting and feedback collection
  - Integration with notification systems

### Product Agent

- **Purpose**: Transforms unstructured requirements into structured specifications
- **Interfaces**:
  - Receives tasks from tracking system
  - Updates task status and details
  - Submits generated specifications for review
  - Requests clarifications when needed
- **Responsibilities**:
  - Analyze product requirements documents from git
  - Generate structured specifications
  - Create acceptance criteria
  - Request human feedback when needed

### Coding Agent

- **Purpose**: Generates code based on structured requirements
- **Interfaces**:
  - Receives tasks from tracking system
  - Updates task status and progress
  - Commits code to repository
  - Creates tests and documentation
- **Responsibilities**:
  - Implement features according to specifications
  - Generate appropriate tests
  - Document code and implementation details
  - Submit implementation for review

## System Interactions

### Task Lifecycle Flow

```mermaid
stateDiagram-v2
    [*] --> VerifyingPRD
    VerifyingPRD --> VerifyingAcceptanceCriteria: PRD validated
    VerifyingAcceptanceCriteria --> VerifyingArchitecture: Criteria validated
    VerifyingArchitecture --> VerifyingExecutionPlan: Architecture validated
    VerifyingExecutionPlan --> QueuedForDevelopment: Plan validated
    QueuedForDevelopment --> InDevelopment: Picked up by Coding Agent
    InDevelopment --> CodeReview: Implementation complete
    CodeReview --> Testing: Code validated
    Testing --> ReadyForDeployment: Tests passed
    ReadyForDeployment --> Deployed: Deployment complete
    Deployed --> [*]
    
    VerifyingPRD --> Blocked: Issues found
    VerifyingAcceptanceCriteria --> Blocked: Issues found
    VerifyingArchitecture --> Blocked: Issues found
    VerifyingExecutionPlan --> Blocked: Issues found
    InDevelopment --> Blocked: Implementation issues
    CodeReview --> InDevelopment: Changes requested
    Testing --> InDevelopment: Tests failed
    
    Blocked --> VerifyingPRD: Issues resolved
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant HI as Human Interface
    participant TTS as Task Tracking System
    participant PA as Product Agent
    participant CA as Coding Agent
    participant Git as Git Repository
    
    User->>HI: Submit requirements
    HI->>Git: Store PRD as markdown
    HI->>TTS: Create task with PRD link
    TTS->>PA: Assign for PRD verification
    PA->>Git: Fetch PRD markdown
    PA->>TTS: Update status (VerifyingPRD)
    PA->>TTS: Update status (VerifyingAcceptanceCriteria)
    PA->>HI: Request clarification (if needed)
    User->>HI: Provide clarification
    HI->>TTS: Update task
    PA->>TTS: Submit structured requirements
    TTS->>HI: Request validation
    User->>HI: Approve requirements
    HI->>TTS: Update status (VerifyingArchitecture)
    
    TTS->>CA: Assign for architecture proposal
    CA->>TTS: Submit architecture plan
    TTS->>HI: Request architecture validation
    User->>HI: Approve architecture
    HI->>TTS: Update status (VerifyingExecutionPlan)
    
    CA->>TTS: Submit execution plan
    TTS->>HI: Request plan validation
    User->>HI: Approve execution plan
    HI->>TTS: Update status (QueuedForDevelopment)
    
    TTS->>CA: Assign for development
    CA->>TTS: Update status (InDevelopment)
    CA->>Git: Commit code
    CA->>TTS: Update status (CodeReview)
    TTS->>HI: Request code review
    User->>HI: Approve code
    HI->>TTS: Update status (Testing)
    
    CA->>TTS: Submit test results
    TTS->>HI: Present test results
    User->>HI: Approve for deployment
    HI->>TTS: Update status (ReadyForDeployment)
```

## Integration Points

### Git Integration

- **PRD Storage**: 
  - PRDs stored as markdown files in git repository
  - Versioned alongside code
  - Referenced by direct links in tasks

- **Code Storage**:
  - Generated code committed to repositories
  - Includes documentation and tests
  - PR-based review workflow

### Notification System

- Alerts stakeholders of status changes
- Notifies when human validation is required
- Provides updates on task progress

### Testing Framework Integration

- Runs tests on generated code
- Reports results to tracking system
- Maintains test history and metrics

## Security Considerations

- Authentication and authorization for all interactions
- Audit logging of status changes and approvals
- Secure storage of sensitive requirements
- Isolation of AI agent operations

## Implementation Guidelines

- Use webhook-based integrations between systems
- Implement event-driven notification system
- Store task history for traceability
- Provide robust API for extensions 