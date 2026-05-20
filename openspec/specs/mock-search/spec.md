# Mock Search Specification

## Purpose

Defines the mock search mode for the `internet_search` tool, enabling simulated search results when Tavily API is unavailable or mock mode is explicitly enabled.

## Requirements

### Requirement: Mock Search Mode
The `internet_search` tool SHALL return simulated search results when Tavily API key is not available or mock mode is explicitly enabled.

#### Scenario: Auto-detect missing API key
- **WHEN** `TAVILY_API_KEY` environment variable is not set
- **THEN** `internet_search` returns mock results without calling Tavily API

#### Scenario: Explicit mock mode via config
- **WHEN** `config.search.mock` is set to `true`
- **THEN** `internet_search` returns mock results even if API key is present

#### Scenario: Normal mode with valid API key
- **WHEN** `TAVILY_API_KEY` is set and `config.search.mock` is `false`
- **THEN** `internet_search` calls the real Tavily API

### Requirement: Mock Result Format
Mock search results SHALL match the structure of real Tavily search results to ensure agent behavior is consistent between mock and real modes.

#### Scenario: Mock result structure matches Tavily
- **WHEN** mock mode returns search results
- **THEN** each result contains `title`, `url`, `content`, and `score` fields

#### Scenario: Mock results are multi-source
- **WHEN** mock mode is triggered
- **THEN** at least 3 mock results are returned with different titles and content to simulate real search diversity
