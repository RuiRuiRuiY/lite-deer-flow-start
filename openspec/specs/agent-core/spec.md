# Agent Core Specification

## Purpose

Defines the core agent architecture including the agent factory, lead agent, sub-agents, filesystem backend, and skills integration for the research and report workflow.

## Requirements

### Requirement: Agent Factory
The system SHALL provide a `create_lead_agent(config: dict)` function that returns a configured Deep Agent instance with lead agent, two sub-agents (research-agent and report-agent), FilesystemBackend, and skills integration.

#### Scenario: Factory creates agent with all components
- **WHEN** `create_lead_agent(config)` is called with valid config dict
- **THEN** the returned agent has lead agent with system prompt, research-agent sub-agent, report-agent sub-agent, FilesystemBackend, and skills loaded

#### Scenario: Factory creates workspace directory
- **WHEN** `create_lead_agent(config)` is called and the workspace directory does not exist
- **THEN** the factory creates the directory before initializing FilesystemBackend

### Requirement: Lead Agent Configuration
The lead agent SHALL be created with a system prompt that instructs it to delegate research tasks to research-agent and report writing to report-agent, using the `task()` tool.

#### Scenario: Lead agent delegates to sub-agents
- **WHEN** user asks a research question
- **THEN** the lead agent uses `task()` to delegate to research-agent first, then report-agent

### Requirement: Research Sub-Agent
The research-agent SHALL have access to the `internet_search` tool and file system tools (read_file, write_file) for gathering information and writing research notes.

#### Scenario: Research agent searches and writes
- **WHEN** research-agent receives a research task
- **THEN** it uses `internet_search` to find information and `write_file` to save research notes

### Requirement: Report Sub-Agent
The report-agent SHALL have access to file system tools (read_file, write_file, edit_file) for reading research notes and writing structured reports.

#### Scenario: Report agent reads and writes
- **WHEN** report-agent receives a report writing task
- **THEN** it uses `read_file` to read research notes and `write_file` to write the final report

### Requirement: FilesystemBackend Integration
The agent SHALL use `FilesystemBackend(root_dir="data/workspace", virtual_mode=True)` to restrict file operations to the workspace directory.

#### Scenario: File operations are restricted to workspace
- **WHEN** agent attempts to access files outside the workspace directory
- **THEN** the operation is blocked by virtual_mode

### Requirement: Skills System
The agent SHALL load skills from SKILL.md files in `backend/app/skills/research/` and `backend/app/skills/report/` directories.

#### Scenario: Skills are loaded at agent creation
- **WHEN** `create_lead_agent(config)` is called
- **THEN** research and report SKILL.md files are loaded and available to respective sub-agents
