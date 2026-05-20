# Config System Specification

## Purpose

Defines the configuration loading and extraction system for models, sandbox, search, and skills settings using YAML configuration files.

## Requirements

### Requirement: YAML Config Loading
The system SHALL provide a `load_config(path: str) -> dict` function that reads a YAML configuration file and returns its contents as a Python dictionary.

#### Scenario: Valid config file loads successfully
- **WHEN** `load_config("config.yaml")` is called with a valid YAML file
- **THEN** the function returns a dict with all configuration sections (models, search, sandbox, skills)

#### Scenario: Missing config file raises error
- **WHEN** `load_config("nonexistent.yaml")` is called
- **THEN** the function raises a FileNotFoundError with a clear message

### Requirement: Model Config Extraction
The system SHALL extract model configuration from `config.models.primary` section including provider, model name, base_url, and api_key_env name.

#### Scenario: Model config extracted from YAML
- **WHEN** config contains `models.primary` with provider, model, base_url, api_key_env
- **THEN** the extracted config can be passed to `init_chat_model()` with correct parameters

#### Scenario: API key resolved from environment
- **WHEN** config specifies `api_key_env: "DASHSCOPE_API_KEY"`
- **THEN** the actual API key is read from `os.getenv("DASHSCOPE_API_KEY")`

### Requirement: Sandbox Config Extraction
The system SHALL extract sandbox configuration from `config.sandbox` section including type and virtual_mode settings.

#### Scenario: FilesystemBackend config extracted
- **WHEN** config contains `sandbox.type: "filesystem"` and `sandbox.virtual_mode: true`
- **THEN** the factory creates `FilesystemBackend(root_dir=..., virtual_mode=True)`

### Requirement: Search Config Extraction
The system SHALL extract search configuration from `config.search` section including primary search engine and mock mode flag.

#### Scenario: Search config with mock flag
- **WHEN** config contains `search.primary: "tavily"` and `search.mock: false`
- **THEN** the mock mode is determined by both the flag and API key availability
