## ADDED Requirements

### Requirement: CLI Entry Point
The system SHALL provide a CLI entry point at `backend/main.py` that loads configuration, creates the agent, accepts user input, runs the agent workflow, and prints the result.

#### Scenario: User runs CLI and gets report
- **WHEN** user runs `python main.py` and enters a research question
- **THEN** the agent completes the research and report workflow, and the terminal prints the final report

#### Scenario: CLI handles empty input
- **WHEN** user runs `python main.py` and enters empty input
- **THEN** the CLI prompts again or exits gracefully with an error message

### Requirement: Async Execution
The CLI SHALL use async execution (`ainvoke`) to run the agent workflow.

#### Scenario: Agent runs asynchronously
- **WHEN** `main.py` invokes the agent
- **THEN** it uses `asyncio.run()` and `agent.ainvoke()` for async execution

### Requirement: Workspace File Output
The agent SHALL write research notes and final report to files in the workspace directory during execution.

#### Scenario: Research notes written
- **WHEN** research-agent completes its task
- **THEN** research notes are written to `data/workspace/research_notes.md`

#### Scenario: Final report written
- **WHEN** report-agent completes its task
- **THEN** the final report is written to `data/workspace/report.md`
