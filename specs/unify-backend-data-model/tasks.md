---

description: "Task list for Unify Backend Data Model feature implementation"
---

# Tasks: Unify Backend Data Model

**Input**: Design documents from `/specs/unify-backend-data-model/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Test-Driven Development (TDD) is mandatory per the constitution. Tests MUST be written before implementation for all new logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Paths shown below assume root-level backend files (`app.py`, `models.py`, `schemas.py`).

## Phase 1: Foundational - User Story 1 (Priority: P1) 🎯 MVP
**Goal**: Establish a consistent and centralized data model definition (`Student` and `Todo`) across the backend by refactoring `app.py` to use `models.py` and `schemas.py` as the single source of truth.

**Independent Test**: Running the backend `app.py` and verifying that the `/todos/` and `/students/` endpoints function as expected, including successful interaction with the `app/todos/page.tsx` frontend component. Unit tests for `models.py` and `schemas.py` ensure structural correctness.

### Tests for Data Model Unification (MANDATORY) ⚠️
> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T001 [P] [US1] Write unit tests in `tests/test_models.py` to ensure `Student` and `Todo` SQLModel definitions are correctly transferred to `models.py`, including their table name and column types. These tests should initially fail because the models are not yet in `models.py`.
- [ ] T002 [P] [US1] Write unit tests in `tests/test_schemas.py` to ensure `Student` and `Todo` Pydantic schemas are correctly defined in `schemas.py` and validate data as expected. These tests should initially fail.
- [ ] T003 [P] [US1] Write an integration test in `tests/test_app_integration.py` to verify that `app.py` can successfully create, read, update, and delete `Todo` items using the *soon-to-be-unified* models, and that the existing frontend component `app/todos/page.tsx` can consume these correctly. This test will likely require a mocked or temporary database setup. This test should initially fail or demonstrate incorrect behavior.

### Implementation for Data Model Unification

- [ ] T004 [US1] Identify and extract the `Todo` SQLModel definition from `app.py` and move it, along with its associated table creation/initialization logic, to `models.py`. Ensure the `SQLModel` base class is correctly imported.
- [ ] T005 [US1] Identify and extract the `Student` SQLModel definition (if fully present/intended) from `app.py` and move it, along with its associated table creation/initialization logic, to `models.py`. Ensure the `SQLModel` base class is correctly imported.
- [ ] T006 [P] [US1] Create or refine the `Todo` Pydantic schemas (e.g., `TodoCreate`, `TodoRead`) in `schemas.py` to precisely align with the `Todo` SQLModel definition in `models.py`.
- [ ] T007 [P] [US1] Create or refine the `Student` Pydantic schemas (e.g., `StudentCreate`, `StudentRead`) in `schemas.py` to precisely align with the `Student` SQLModel definition in `models.py`.
- [ ] T008 [US1] Modify `app.py` to import the `Student` and `Todo` SQLModels directly from `models.py`.
- [ ] T009 [US1] Modify `app.py` to import the `Student` and `Todo` Pydantic schemas directly from `schemas.py`.
- [ ] T010 [US1] Remove any redundant or conflicting `Todo` and `Student` model definitions or related classes/logic that were previously defined directly within `app.py`.
- [ ] T011 [US1] Remove all occurrences of `StudentClass` related models, schemas, and any associated logic (e.g., `nameplz` field handling) from `models.py`, `schemas.py`, and `app.py`. This ensures complete deprecation.
- [ ] T012 [US1] Review and update all FastAPI API endpoints in `app.py` (e.g., `/todos/`, `/students/`) to ensure they correctly use the newly imported `Student` and `Todo` models and schemas for request bodies, response models, and database interactions.
- [ ] T013 [US1] Run the FastAPI application (`app.py`) locally and manually verify that `app/todos/page.tsx` (the frontend) can still fetch, add, and delete todo items without errors.
- [ ] T014 [US1] Run all created unit and integration tests (T001, T002, T003) and ensure they pass, confirming the data model unification and functionality.

---

## Parallel Opportunities

- Tasks T001, T002, T003 (test creation) can be worked on in parallel.
- Tasks T004-T005 (model extraction) and T006-T007 (schema creation) can be done in parallel once the initial extraction is planned.
- The remaining tasks are largely sequential as they depend on the updated `models.py` and `schemas.py`.
