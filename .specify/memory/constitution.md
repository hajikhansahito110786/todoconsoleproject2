<!--
Sync Impact Report:
- Version change: none -> 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] -> I. API-First Development
  - [PRINCIPLE_2_NAME] -> II. Clear Interface Contracts
  - [PRINCIPLE_3_NAME] -> III. Test-Driven Development (TDD)
  - [PRINCIPLE_4_NAME] -> IV. Comprehensive Testing
  - [PRINCIPLE_5_NAME] -> V. Simplicity and YAGNI
  - [PRINCIPLE_6_NAME] -> VI. Clear Versioning
- Added sections:
  - Technology Stack
  - Development Workflow
- Removed sections: none
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Set the actual ratification date.
-->
# tododswithsqlmodelneon5withfrontendnextjs Constitution

## Core Principles

### I. API-First Development
Every new feature or significant change must begin with a clear, well-documented API design. The backend API serves as the core contract, and frontend development should proceed based on this contract, using mock data until the API is implemented.

### II. Clear Interface Contracts
All interfaces, whether backend REST APIs, component props, or function signatures, must be clearly defined and strongly typed. OpenAPI specifications for the backend and TypeScript for the frontend are mandatory.

### III. Test-Driven Development (TDD)
TDD is mandatory for all new backend logic and critical frontend components. Tests must be written before the implementation, they must initially fail, and then the code should be written to make them pass. The Red-Green-Refactor cycle is a core practice.

### IV. Comprehensive Testing
The project must maintain a high level of test coverage, including:
- **Unit Tests:** For individual functions and components.
- **Integration Tests:** To verify interactions between different parts of the application (e.g., API and database).
- **End-to-End (E2E) Tests:** To simulate user flows.

### V. Simplicity and YAGNI
We adhere to the "You Aren't Gonna Need It" (YAGNI) principle. Do not add functionality or complexity unless it is required by the current specification. Solutions should be as simple as possible.

### VI. Clear Versioning
The project and its APIs must follow Semantic Versioning (MAJOR.MINOR.PATCH). All breaking changes must be carefully managed, documented, and communicated.

## Technology Stack

The project utilizes a specific technology stack. Adherence to these technologies is required to maintain consistency and expertise.
- **Backend:** Python with FastAPI and SQLModel.
- **Database:** PostgreSQL (specifically via Neon).
- **Frontend:** Next.js with TypeScript and React.
- **Styling:** Tailwind CSS.

## Development Workflow

All development must follow a structured workflow to ensure quality and collaboration.
- **Branches:** All work must be done in feature branches, prefixed with a type (e.g., `feature/`, `fix/`, `chore/`).
- **Pull Requests (PRs):** Changes are merged into the main branch via Pull Requests.
- **Code Reviews:** Every PR must be reviewed and approved by at least one other developer before merging.
- **Continuous Integration (CI):** All commits pushed to a PR must pass automated checks, including linting, type-checking, and tests.

## Main Focus: Core Entities

To ensure clarity and focus, the project revolves around two primary data entities:
- **Student:** Represents the user or owner of a set of tasks.
- **Todo:** Represents a single task item associated with a Student.

All feature development should be framed in the context of how it creates, reads, updates, or deletes these core entities.

## Todo App Feature Progression

Development of the Todo application will follow a phased approach. Features are grouped into tiers to ensure a stable MVP can be built first, with more advanced features added in subsequent phases.

### Basic Level (Core Essentials)
These features form the foundational MVP. They must be implemented first.
- **Add Task:** Create new todo items.
- **Delete Task:** Remove tasks from the list.
- **Update Task:** Modify existing task details (e.g., title, description).
- **View Task List:** Display all tasks for a given student.
- **Mark as Complete:** Toggle a task's completion status.

### Intermediate Level (Organization & Usability)
These features should be implemented after the Basic Level is complete to enhance the user experience.
- **Priorities & Tags/Categories:** Assign priority levels (e.g., high/medium/low) or categorical labels (e.g., work/home) to tasks.
- **Search & Filter:** Implement functionality to search for tasks by keyword and filter them by status, priority, or due date.
- **Sort Tasks:** Allow users to reorder the task list based on criteria like due date, priority, or alphabetical order.

## Governance

This Constitution is the single source of truth for development standards and practices. It supersedes all other conventions. Amendments to this constitution require a documented proposal, review, and an approved migration plan for existing code if necessary. All code reviews must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): 2026-01-05 | **Last Amended**: 2026-01-05