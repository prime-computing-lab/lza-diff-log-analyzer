# LZA Diff Analyzer

An intelligent AWS Landing Zone Accelerator diff log analyzer powered by Large Language Models.

## Overview

This tool analyzes CloudFormation diff logs generated during AWS Landing Zone Accelerator (LZA) upgrades to identify potential risks, security implications, and provide actionable recommendations.

## Features

- **Cloud Administrator Friendly**: Human-readable summaries designed for cloud operations teams
- **Interactive Q&A Mode**: Ask natural language questions about your LZA changes
- **Multi-LLM Support**: Works with local models (via Ollama) with cloud API support planned (OpenAI, Anthropic)
- **Intelligent Risk Analysis**: Automated identification of high-risk changes with business context
- **LZA-Specific Intelligence**: Recognizes common LZA upgrade patterns and provides relevant guidance
- **Executive Summaries**: Clear explanations of what changes mean and what actions to take
- **Smart Recommendations**: Context-aware suggestions for change management and testing

## Installation

### Prerequisites

- Python 3.10+
- [UV](https://docs.astral.sh/uv/) (recommended for fast package management)

### Setup with UV (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd lza-diff-analyzer

# Install project with UV (creates venv automatically)
uv sync

# For all features (includes LLM and development tools)
uv sync --extra dev --extra llm

# Activate the environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Alternative Setup (Standard pip)

```bash
# Clone the repository
git clone <repository-url>
cd lza-diff-analyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# For all features (includes LLM and development tools)  
pip install -e ".[dev,llm]"
```

## Quick Start

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Basic analysis with cloud admin-friendly output (LLM enabled by default)
lza-analyze --input-dir /path/to/diff-logs

# Technical detailed output (for verbose analysis)
lza-analyze --input-dir /path/to/diff-logs --verbose

# Rule-based analysis only (disable LLM)
lza-analyze --input-dir /path/to/diff-logs --disable-llm

# Generate specific output format
lza-analyze --input-dir /path/to/diff-logs --format yaml

# Generate comprehensive HTML reports
lza-analyze --input-dir /path/to/diff-logs --generate-reports

# Specify a particular LLM provider
lza-analyze --input-dir /path/to/diff-logs --llm-provider anthropic
```

## Sample Output

### Cloud Administrator-Friendly Analysis
```
🔍 EXECUTIVE SUMMARY
Your LZA upgrade from 1.10.0 to 1.12.1 affects 74 stacks across multiple accounts.
Total changes detected: 225 resources, 462 IAM modifications.

⚠️  KEY CONCERNS (Requires Your Review):
1. IAM Permission Changes (258 findings)
   └─ Why: Roles and policies are being modified during upgrade
   └─ Action: Review cross-account access in DependenciesStack

🎯 IMMEDIATE ACTIONS:
□ Test IAM changes in non-production environment first
□ Review IAM changes for unintended privilege escalation
□ Validate automation scripts work with updated parameters
□ Backup current configurations before proceeding

💡 CONTEXT
This appears to be a standard LZA upgrade. High finding counts (331) are
normal due to IAM management complexity and version parameter updates.
Focus on the prioritized items above rather than the total count.
```

### Interactive Analysis Features
```bash
# The analyzer provides interactive analysis capabilities when LLM is enabled
$ lza-analyze --input-dir ./diff-logs --verbose

🔍 EXECUTIVE SUMMARY
Your LZA upgrade from 1.10.0 to 1.12.1 affects 74 stacks across multiple accounts.
Total changes detected: 225 resources, 462 IAM modifications.

⚠️ KEY CONCERNS (Requires Your Review):
1. IAM Permission Changes (258 findings)
   └─ Why: Roles and policies are being modified during upgrade
   └─ Action: Review cross-account access in DependenciesStack

🤖 AI-POWERED INSIGHTS
The main IAM concerns in your LZA upgrade are:

1. **Cross-account role modifications** in DependenciesStack
   - These affect access between Log Archive, Audit, and workload accounts
   - Test in non-production to ensure connectivity remains intact

2. **Service role permission updates** 
   - LZA pipeline roles are getting new permissions for v1.12.1 features
   - Generally safe but verify no unexpected admin access

Recommended action: Compare role policies before/after in a test environment first.
```

## Testing

```bash
# Run tests (if available)
uv run pytest

# Run linting
uv run ruff check

# Run type checking
uv run mypy src/
```

## Development

This project is built in phases:

1. **Phase 1**: Foundation & Log Parsing ✅
2. **Phase 2**: LLM Abstraction Layer ✅ (MCP Integration - Planned)
3. **Phase 3**: Risk Analysis Engine ✅ (MCP Tools - Planned)
4. **Phase 4**: CLI & User Experience ✅ (Interactive Mode - In Development)
5. **Phase 5**: Advanced Analysis & Reporting ✅ (Advanced Features - In Development)

## Configuration

The LLM configuration is located at `config/llm_config.yaml`. Here's the current structure:

```yaml
# LZA Diff Analyzer - LLM Configuration
default_provider: ollama
max_retries: 3
retry_delay: 1.0

# Fallback chain - providers will be tried in this order
fallback_chain:
  - ollama
  # - openai     # Will be enabled when implementation is complete
  # - anthropic  # Will be enabled when implementation is complete

providers:
  ollama:
    provider: ollama
    model: "your model" 
    temperature: 0.1
    max_tokens: 12288
    timeout: 120
    base_url: "http://localhost:11434"
    enabled: true
    additional_params:
      num_predict: 12288
      top_k: 30
      top_p: 0.85

  # ✅ Cloud providers - Fully implemented (enabled when API keys are set):
  # openai:
  #   provider: openai
  #   model: "gpt-4o-mini"
  #   temperature: 0.1
  #   max_tokens: 4096
  #   timeout: 30
  #   api_key: ${OPENAI_API_KEY}  # Set via environment variable
  #   enabled: false  # Auto-enabled when API key is available

  # anthropic:
  #   provider: anthropic  
  #   model: "claude-3-haiku-20240307"
  #   temperature: 0.1
  #   max_tokens: 4096
  #   timeout: 30
  #   api_key: ${ANTHROPIC_API_KEY}  # Set via environment variable
  #   enabled: false  # Auto-enabled when API key is available
```

**Current LLM Support Status**:
- ✅ **Ollama**: Fully implemented and production ready
- ✅ **OpenAI**: Fully implemented (requires API key)
- ✅ **Anthropic**: Fully implemented (requires API key)

### Setting up Ollama

```bash
# Start Ollama service
ollama serve

# Check available models
ollama list

# Pull a model if needed (examples)
ollama pull qwen2.5:7b          # Fast, lightweight model
ollama pull qwen3:30b-a3b       # High-quality model (current production model)
ollama pull llama3.2:latest     # Alternative model option
```

### Setting up Cloud Providers

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**Note**: Cloud providers are enabled automatically when API keys are set via environment variables. The configuration file shows them as commented out, but they will be activated when the corresponding environment variables are detected.

## License

MIT License - see LICENSE file for details.