# AI-Driven Development Pipeline: Component Architecture

## Introduction

This document outlines the key components of the AI-driven development pipeline, focusing on their interfaces and interaction patterns. The architecture is designed to be simple and practical, avoiding unnecessary complexity.

## Core Components

The AI-driven development pipeline consists of the following core components:

```mermaid
graph TD
    HI[Human Interface]
    TTS[Task Tracking System]
    OA[Orchestrator Agent]
    PA[Product Agent]
    CA[Coding Agent]
    
    HI -->|1. Submit Requirements| TTS
    TTS -->|2. Notify New Task| OA
    OA -->|3. Assign Task| PA
    PA -->|4. Return Processed Requirements| OA
    OA -->|5. Update Task Status| TTS
    HI -->|6. Review & Validate| TTS
    OA -->|7. Assign Implementation| CA
    CA -->|8. Return Generated Code| OA
    OA -->|9. Request Human Review| HI
```

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
  - PRD Needs Update - Feedback indicates PRD requires changes
  - Verifying Acceptance Criteria - Ensuring clear success metrics
  - Acceptance Criteria Need Update - Feedback indicates criteria require refinement
  - Verifying Architecture - Reviewing the proposed technical approach
  - Architecture Needs Revision - Feedback indicates architecture plan needs changes
  - Verifying Execution Plan - Evaluating the implementation strategy
  - Execution Plan Needs Revision - Feedback indicates execution plan needs changes
  - Queued for Development - Ready to be picked up by coding agent
  - In Development - Currently being implemented
  - Implementation Needs Fixes - Code requires changes based on feedback
  - Code Review - Awaiting human validation
  - Testing - Undergoing automated testing
  - Tests Need Updates - Test failures require addressing
  - Ready for Deployment - Verified and ready to deploy
  - Deployed - Live in production
- **Key Features**:
  - Git integration for PRD linking (PRDs stored as markdown files)
  - Status tracking with timestamps
  - Assignment functionality
  - Commenting and feedback collection
  - Integration with notification systems

### Orchestrator Agent

The Orchestrator Agent manages workflow progression and task assignments between the specialized AI agents.

**Key Responsibilities:**
- Monitor the Task Tracking System for new or updated tasks
- Determine next steps in the workflow based on task state
- Assign tasks to appropriate specialized agents (Product Agent, Coding Agent)
- Update task status based on agent responses
- Coordinate human validation requests at checkpoints

**Implementation Considerations:**
- Event-driven design to react to task status changes
- Decision engine for workflow routing
- Retry and error handling logic
- Monitoring for agent performance and availability

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
    
    VerifyingPRD --> PRDNeedsUpdate: Feedback received
    PRDNeedsUpdate --> VerifyingPRD: Updated
    
    VerifyingPRD --> VerifyingAcceptanceCriteria: PRD validated
    
    VerifyingAcceptanceCriteria --> AcceptanceCriteriaNeedUpdate: Feedback received
    AcceptanceCriteriaNeedUpdate --> VerifyingAcceptanceCriteria: Updated
    
    VerifyingAcceptanceCriteria --> VerifyingArchitecture: Criteria validated
    
    VerifyingArchitecture --> ArchitectureNeedsRevision: Feedback received
    ArchitectureNeedsRevision --> VerifyingArchitecture: Updated
    
    VerifyingArchitecture --> VerifyingExecutionPlan: Architecture validated
    
    VerifyingExecutionPlan --> ExecutionPlanNeedsRevision: Feedback received
    ExecutionPlanNeedsRevision --> VerifyingExecutionPlan: Updated
    
    VerifyingExecutionPlan --> QueuedForDevelopment: Plan validated
    QueuedForDevelopment --> InDevelopment: Picked up by Coding Agent
    
    InDevelopment --> ImplementationNeedsFixes: Issues found
    ImplementationNeedsFixes --> InDevelopment: Fixed
    
    InDevelopment --> CodeReview: Implementation complete
    CodeReview --> ImplementationNeedsFixes: Changes requested
    
    CodeReview --> Testing: Code validated
    Testing --> TestsNeedUpdates: Tests failed
    TestsNeedUpdates --> Testing: Fixed
    
    Testing --> ReadyForDeployment: Tests passed
    ReadyForDeployment --> Deployed: Deployment complete
    Deployed --> [*]
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant HI as Human Interface
    participant TTS as Task Tracking System
    participant OA as Orchestrator Agent
    participant PA as Product Agent
    participant CA as Coding Agent
    participant Git as Git Repository
    
    User->>HI: Submit requirements
    HI->>Git: Store PRD as markdown
    HI->>TTS: Create task with PRD link
    TTS->>OA: Notify of new task
    OA->>PA: Assign for PRD verification
    PA->>Git: Fetch PRD markdown
    OA->>TTS: Update status (VerifyingPRD)
    
    alt PRD needs clarification
        PA->>OA: Report clarification needed
        OA->>HI: Request clarification
        User->>HI: Provide feedback
        HI->>OA: Submit clarification
        OA->>TTS: Update status (PRDNeedsUpdate)
        OA->>PA: Forward clarification
        PA->>Git: Update PRD
        OA->>TTS: Update status (VerifyingPRD)
    end
    
    PA->>OA: Submit structured requirements
    OA->>TTS: Update status (VerifyingAcceptanceCriteria)
    
    alt Acceptance criteria need refinement
        OA->>HI: Request feedback on criteria
        User->>HI: Provide feedback
        HI->>OA: Submit feedback
        OA->>TTS: Update status (AcceptanceCriteriaNeedUpdate)
        OA->>PA: Request criteria updates
        PA->>OA: Submit updated criteria
        OA->>TTS: Update status (VerifyingAcceptanceCriteria)
    end
    
    OA->>HI: Request requirements validation
    User->>HI: Approve requirements
    HI->>OA: Confirm approval
    OA->>TTS: Update status (VerifyingArchitecture)
    
    OA->>CA: Assign for architecture proposal
    CA->>OA: Submit architecture plan
    OA->>HI: Request architecture validation
    
    alt Architecture needs revision
        User->>HI: Provide architecture feedback
        HI->>OA: Submit feedback
        OA->>TTS: Update status (ArchitectureNeedsRevision)
        OA->>CA: Request architecture update
        CA->>OA: Submit updated architecture
        OA->>TTS: Update status (VerifyingArchitecture)
    end
    
    User->>HI: Approve architecture
    HI->>OA: Confirm approval
    OA->>TTS: Update status (VerifyingExecutionPlan)
    
    OA->>CA: Request execution plan
    CA->>OA: Submit execution plan
    OA->>HI: Request plan validation
    
    alt Execution plan needs revision
        User->>HI: Provide execution plan feedback
        HI->>OA: Submit feedback
        OA->>TTS: Update status (ExecutionPlanNeedsRevision)
        OA->>CA: Request plan update
        CA->>OA: Submit updated plan
        OA->>TTS: Update status (VerifyingExecutionPlan)
    end
    
    User->>HI: Approve execution plan
    HI->>OA: Confirm approval
    OA->>TTS: Update status (QueuedForDevelopment)
    
    OA->>CA: Assign for development
    OA->>TTS: Update status (InDevelopment)
    
    alt Implementation issues
        CA->>OA: Report implementation issues
        OA->>TTS: Update status (ImplementationNeedsFixes)
        CA->>Git: Fix code
        CA->>OA: Report fixes complete
        OA->>TTS: Update status (InDevelopment)
    end
    
    CA->>Git: Commit code
    CA->>OA: Report code completion
    OA->>TTS: Update status (CodeReview)
    OA->>HI: Request code review
    
    alt Code changes requested
        User->>HI: Request code changes
        HI->>OA: Submit change requests
        OA->>TTS: Update status (ImplementationNeedsFixes)
        OA->>CA: Request code updates
        CA->>Git: Update code
        CA->>OA: Report updates complete
        OA->>TTS: Update status (CodeReview)
    end
    
    User->>HI: Approve code
    HI->>OA: Confirm approval
    OA->>TTS: Update status (Testing)
    
    OA->>CA: Request testing
    CA->>OA: Submit test results
    
    alt Tests failed
        OA->>TTS: Update status (TestsNeedUpdates)
        OA->>CA: Request fixes
        CA->>Git: Fix issues
        CA->>OA: Report fixes complete
        OA->>TTS: Update status (Testing)
    end
    
    OA->>HI: Present test results
    User->>HI: Approve for deployment
    HI->>OA: Confirm approval
    OA->>TTS: Update status (ReadyForDeployment)
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