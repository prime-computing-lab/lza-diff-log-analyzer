# LZA Diff Analyzer - Component Guide

## Overview

This document provides detailed information about each component in the LZA Diff Analyzer, including its purpose, functionality, key methods, and maintenance considerations. This guide is essential for DevOps engineers and software engineers who need to maintain, troubleshoot, or extend the system.

## Table of Contents

1. [CLI Interface](#cli-interface)
2. [Data Models](#data-models)
3. [Parsing Layer](#parsing-layer)
4. [Analysis Engine](#analysis-engine)
5. [LLM Integration](#llm-integration)
6. [Risk Analyzers](#risk-analyzers)
7. [Reporting System](#reporting-system)
8. [Interactive Session](#interactive-session)
9. [Configuration Management](#configuration-management)
10. [Utilities & Helpers](#utilities--helpers)

---

## CLI Interface

### Location: `src/cli/simple_main.py`

The command-line interface is the primary entry point for users interacting with the system. The CLI has been simplified and streamlined for better user experience.

#### Key Components

**Main CLI Command**
```python
@click.command()
@click.version_option(version="0.1.0")
def main(...):
    """LZA Diff Analyzer - Analyze CloudFormation diff logs with AI assistance"""
```

**Key Options**:
- `--input-dir, -i`: Directory containing diff log files (required)
- `--output-dir, -o`: Output directory for analysis results
- `--format, -f`: Output format (json, yaml, html)
- `--disable-llm`: Disable LLM-powered analysis (LLM enabled by default)
- `--llm-provider`: Specify LLM provider (ollama, openai, anthropic)
- `--generate-reports`: Generate comprehensive HTML reports
- `--verbose, -v`: Enable verbose output

#### Critical Functions

**cli() Command**
- **Purpose**: Main unified command that performs comprehensive analysis of diff logs
- **Input**: Directory containing .diff files (via `--input-dir`)
- **Output**: Analysis results in JSON/YAML/HTML formats
- **Key Features**:
  - LLM disable option (`--disable-llm`, enabled by default)
  - Multiple output formats (`--format json|yaml|html`)
  - Report generation (`--generate-reports`)
  - LLM provider selection (`--llm-provider ollama|openai|anthropic`)
  - Progress tracking with Rich
  - Comprehensive error handling

#### Error Handling

```python
try:
    # Main analysis workflow
    loop.run_until_complete(_run_unified_analysis(
        input_dir, output_dir, format, enable_llm, disable_llm, 
        llm_provider, generate_reports, no_interactive, verbose
    ))
except KeyboardInterrupt:
    console.print("\n👋 Analysis interrupted by user")
except Exception as e:
    console.print(f"[red]Analysis failed: {str(e)}[/red]")
    if verbose:
        console.print(traceback.format_exc())
```

#### Maintenance Notes
- **Async Handling**: Proper event loop management for async operations
- **Resource Cleanup**: Ensures loop closure in finally blocks with task cancellation
- **Progress Indication**: Rich console for user feedback
- **Unified Interface**: Single command with multiple configuration options
- **Flexible Output**: Support for multiple formats and report generation

---

## Data Models

### Location: `src/models/diff_models.py`

Pydantic-based models providing type safety and validation for all data structures.

#### Core Models

**DiffAnalysis**
```python
class DiffAnalysis(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    stack_diffs: List[StackDiff] = Field(default_factory=list)
    total_stacks: int = 0
    total_resources_changed: int = 0
    total_iam_changes: int = 0
```

**StackDiff**
```python
class StackDiff(BaseModel):
    stack_name: str
    resource_changes: List[ResourceChange] = Field(default_factory=list)
    iam_statement_changes: List[IAMStatementChange] = Field(default_factory=list)
    account_id: Optional[str] = None
    region: Optional[str] = None
```

**ResourceChange**
```python
class ResourceChange(BaseModel):
    logical_id: str
    resource_type: str
    change_type: ChangeType
    property_changes: List[PropertyChange] = Field(default_factory=list)
```

#### Resource Categorization System

**ResourceCategorizer Class**
- **Purpose**: Automatically categorizes AWS resources by service patterns
- **Key Innovation**: No hardcoded resource types - uses regex patterns
- **Benefits**: Future-proof for new AWS services

```python
SERVICE_PATTERNS = {
    ResourceCategory.IAM_RESOURCES: [r"^AWS::IAM::"],
    ResourceCategory.SECURITY_RESOURCES: [r"^AWS::KMS::", r"^AWS::SecretsManager::"],
    # ... more patterns
}
```

**Methods**:
- `categorize()`: Returns resource category for any AWS resource type
- `is_security_resource()`: Boolean check for security-related resources
- `get_service_name()`: Extracts AWS service name from resource type

#### Serialization Features

**Custom dict() Method**
```python
def dict(self, **kwargs):
    # Handles datetime serialization and other complex types
    def serialize_objects(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # ... handle other types
```

#### Maintenance Notes
- **Extensibility**: Easy to add new resource categories via configuration
- **Validation**: Pydantic ensures data integrity
- **Serialization**: Custom serialization for JSON/YAML compatibility
- **Performance**: Cached pattern matching for large datasets

---

## Parsing Layer

### Location: `src/parsers/`

Responsible for converting raw diff files into structured data models.

#### DiffParser (`diff_parser.py`)

**Purpose**: Parses CloudFormation diff files into structured objects

**Key Methods**:

```python
def parse_file(self, file_path: Path) -> StackDiff:
    """Parse a single diff file and return StackDiff"""

def parse_directory(self, directory: Path) -> DiffAnalysis:
    """Parse all diff files in a directory"""

def parse_content(self, content: str, filename: str) -> StackDiff:
    """Parse diff content and return StackDiff"""
```

**Parsing Sections**:
- **Template Section**: Description changes and metadata
- **IAM Statement Changes**: Policy and permission modifications
- **Resources Section**: Resource additions, modifications, deletions

**IAM Parsing Logic**:
```python
def _parse_iam_statement_row(self, line: str) -> Optional[IAMStatementChange]:
    # Parses table format: │ + │ Resource │ Effect │ Action │ Principal │
    parts = [part.strip() for part in line.split("│")]
    return IAMStatementChange(
        effect=parts[3],
        action=parts[4],
        resource=parts[2],
        principal=parts[5] if len(parts) > 5 else None,
        change_type=change_type
    )
```

#### FileValidator & FileManager (`file_utils.py`)

**FileValidator**
- **Purpose**: Validates input directories and files
- **Features**: 
  - Checks directory existence
  - Validates .diff file presence
  - Provides warnings for unusual patterns

**FileManager**
- **Purpose**: Handles output operations and serialization
- **Key Methods**:
  - `create_output_structure()`: Creates organized output directories
  - `save_analysis()`: Multi-format serialization (JSON, YAML, HTML)

#### Error Resilience

```python
for file_path in diff_files:
    try:
        stack_diff = self.parse_file(file_path)
        analysis.stack_diffs.append(stack_diff)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        continue  # Continue with other files
```

#### Maintenance Notes
- **Regex Patterns**: Update for new diff formats
- **Error Handling**: Individual file failures don't stop processing
- **Metadata Extraction**: Account/region extraction from filenames
- **Performance**: Streaming processing for large files

---

## Analysis Engine

### Location: `src/analyzers/analysis_engine.py`

The central orchestrator that coordinates rule-based and LLM analysis.

#### ComprehensiveAnalysisEngine

**Purpose**: Main analysis coordinator combining multiple analysis methods

**Key Method**:
```python
async def analyze(
    self, 
    diff_analysis: DiffAnalysis, 
    enable_llm: bool = True,
    llm_provider: Optional[str] = None
) -> ComprehensiveAnalysisResult:
```

**Analysis Flow**:
1. **Rule-Based Analysis**: Run all registered analyzers
2. **LLM Analysis**: If enabled, perform AI-powered analysis
3. **Result Combination**: Merge insights from both approaches
4. **Metadata Collection**: Gather analysis statistics

#### LLM Integration

**Provider Management**:
```python
async def _perform_llm_analysis(self, ...):
    # Try preferred provider first, then fallback chain
    providers_to_try = []
    if preferred_provider:
        providers_to_try.append(self.llm_config.get_llm_config(provider_enum))
    providers_to_try.extend(self.llm_config.get_fallback_configs())
```

**Prompt Engineering**:
- **Overall Assessment**: Enterprise-wide impact analysis
- **Network Impact**: Connectivity and routing analysis
- **Security Impact**: Access control and encryption analysis
- **Operational Readiness**: Deployment and maintenance analysis

#### Context Preparation

**Changes Summary**:
```python
def _create_changes_summary(self, diff_analysis: DiffAnalysis) -> str:
    # Creates concise summary for LLM context
    change_categories = {}
    for stack_diff in diff_analysis.stack_diffs:
        for change in stack_diff.resource_changes:
            category = change.parsed_resource_category.value
            # Count adds/modifies/deletes by category
```

#### Maintenance Notes
- **Analyzer Registration**: Easy to add new risk analyzers
- **Provider Fallback**: Robust error handling for LLM failures
- **Prompt Evolution**: Specialized prompts for different analysis types
- **Result Combination**: Intelligent merging of rule-based and AI insights

---

## LLM Integration

### Location: `src/llm/`

Provides unified interface for multiple LLM providers with robust error handling.

#### Base Abstractions (`base.py`)

**BaseLLMProvider**
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Generate a response from the LLM"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
```

**LLMProviderFactory**
```python
@staticmethod
def create_provider(config: LLMConfig) -> BaseLLMProvider:
    if config.provider == LLMProvider.OLLAMA:
        from .ollama_client import OllamaClient
        return OllamaClient(config)
    # ... other providers
```

#### Configuration Management (`config.py`)

**LLMConfigManager**
- **Purpose**: Manages LLM provider configurations and fallback chains
- **Features**:
  - YAML-based configuration
  - Environment variable substitution
  - Provider availability checking
  - Fallback chain management

```python
def get_fallback_configs(self) -> List[LLMConfig]:
    configs = []
    for provider_name in self.fallback_chain:
        provider_enum = LLMProvider(provider_name)
        config = self.get_llm_config(provider_enum)
        if config and config.enabled:
            configs.append(config)
    return configs
```

#### Ollama Client (`ollama_client.py`) ✅ **Fully Implemented**

**Key Features**:
- **Local Model Support**: Integrates with locally running Ollama service
- **Connection Management**: Handles service availability and timeouts
- **Parameter Support**: Model-specific parameters (temperature, top_k, etc.)
- **Production Ready**: Complete error handling and recovery mechanisms

#### OpenAI Client 🔄 **Implementation in Progress**

**Planned Features**:
- **GPT Integration**: GPT-4, GPT-4 Turbo, and GPT-3.5 model support
- **API Key Management**: Secure authentication handling
- **Rate Limiting**: Built-in request throttling and retry logic
- **Status**: Base interface complete, client implementation pending

#### Anthropic Client 🔄 **Implementation in Progress**

**Planned Features**:
- **Claude Integration**: Claude Haiku, Sonnet, and Opus model support
- **Message API**: Latest Anthropic message format support
- **Content Safety**: Built-in content filtering and safety checks
- **Status**: Base interface complete, client implementation pending

#### Error Handling

**LLMError Class**:
```python
class LLMError(Exception):
    def __init__(self, message: str, provider: LLMProvider, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
```

#### Maintenance Notes
- **Provider Addition**: Easy to add new LLM providers
- **Configuration Validation**: Pydantic-based config validation
- **Async Support**: Full async/await integration
- **Error Categorization**: Different error types for different failures

---

## Risk Analyzers

### Location: `src/analyzers/`

Modular risk analysis components that identify specific types of risks.

#### Base Risk Analyzer (`base.py`)

**BaseRiskAnalyzer**
```python
class BaseRiskAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze the diff for risks specific to this analyzer"""
```

**RiskFinding Model**
```python
class RiskFinding(BaseModel):
    finding_id: str
    title: str
    description: str
    risk_level: RiskLevel
    risk_category: RiskCategory
    stack_name: str
    resource_id: str
    recommendations: List[str]
    rollback_steps: List[str]
    confidence_score: float
```

#### Security Risk Analyzer (`security_analyzer.py`)

**Purpose**: Identifies security and access control risks

**Key Risk Categories**:
- **IAM Permission Changes**: Role and policy modifications
- **Encryption Key Changes**: KMS key policy updates
- **Security Resource Deletions**: Critical security service removals
- **Trust Relationship Changes**: Cross-account access modifications

**High-Risk Action Detection**:
```python
self.high_risk_iam_actions = {
    "*", "iam:*", "sts:AssumeRole",
    "organizations:*", "account:*",
    "kms:CreateKey", "kms:DeleteKey",
    # ... more actions
}

def _is_high_risk_action(self, action: str) -> bool:
    # Pattern matching for wildcards and direct matches
    for risk_action in self.high_risk_iam_actions:
        if "*" in risk_action:
            pattern = risk_action.replace("*", ".*")
            if re.match(pattern, action):
                return True
```

#### Network Risk Analyzer (`network_analyzer.py`)

**Purpose**: Identifies network connectivity and routing risks

**Key Focus Areas**:
- **Hub-Spoke Architecture**: Transit Gateway and routing changes
- **Cross-Account Connectivity**: Shared service access
- **VPN/Direct Connect**: On-premises connectivity
- **Security Group Changes**: Access control modifications

#### Operational Risk Analyzer (`operational_analyzer.py`)

**Purpose**: Identifies workload and operational impact risks

**Key Risk Areas**:
- **Data Loss Prevention**: Resource deletion impacts
- **Workload Dependencies**: Service interdependency analysis
- **Scaling and Performance**: Capacity and performance impacts
- **Monitoring and Alerting**: Observability service changes

#### Compliance Risk Analyzer (`compliance_analyzer.py`)

**Purpose**: Identifies regulatory and governance compliance impacts

**Regulatory Frameworks**:
- SOC2 Type II
- PCI-DSS
- GDPR
- HIPAA
- ISO 27001

#### Maintenance Notes
- **Modular Design**: Easy to add new analyzers
- **Risk Scoring**: Consistent scoring across analyzers
- **Framework Updates**: Regular updates for new compliance requirements
- **Pattern Recognition**: Regular updates for new AWS services

---

## Reporting System

### Location: `src/reports/` and `src/formatters/`

Generates stakeholder-appropriate reports and summaries.

#### Enterprise Report Generator (`report_generator.py`)

**Purpose**: Creates comprehensive HTML reports for different audiences

**Report Types**:
- **Executive Summary**: Business-focused risk assessment
- **Technical Report**: Detailed findings for engineers
- **Risk Matrix Report**: Visual risk assessment matrix
- **Compliance Report**: Regulatory impact assessment
- **Full Report**: Comprehensive combined report

**Template System**:
```python
class StringTemplateLoader(BaseLoader):
    """Custom template loader for string templates"""
    
def generate_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
    template = self.jinja_env.get_template('executive_summary')
    exec_data = self._prepare_executive_data(analysis_results)
    return template.render(**exec_data)
```

**Built-in HTML Templates**:
- Professional CSS styling
- Responsive design
- Risk-level color coding
- Interactive elements (future)

#### Admin-Friendly Formatter (`admin_friendly.py`)

**Purpose**: Cloud administrator-focused console output

**Key Features**:
- **Executive Summary**: High-level assessment and metrics
- **Key Concerns**: Prioritized issues requiring attention
- **Immediate Actions**: Actionable checklist
- **Context Explanation**: Why findings matter

**LZA-Specific Intelligence**:
```python
def _detect_version_changes(self, input_analysis) -> tuple:
    # Detects LZA version upgrades from description changes
    old_match = re.search(r'Version (\d+\.\d+\.\d+)', old_val)
    new_match = re.search(r'Version (\d+\.\d+\.\d+)', new_val)
```

**Risk Prioritization**:
```python
def _categorize_concerns(self, findings: List[Dict]) -> Dict[str, List]:
    # Groups findings by impact type
    categories = defaultdict(list)
    priority_order = ["iam_changes", "resource_deletions", "security_configs", "network_changes"]
```

#### Maintenance Notes
- **Template Updates**: HTML templates for visual improvements
- **Stakeholder Feedback**: Regular updates based on user needs
- **Performance**: Efficient template rendering for large reports
- **Accessibility**: Web accessibility standards compliance

---

## Interactive Session

### Location: `src/interactive/simple_session.py`

Provides natural language Q&A interface for detailed analysis exploration.

#### InteractiveSession Class

**Purpose**: AI-powered conversational interface for analysis exploration

**Key Features**:
- **Context Awareness**: Uses analysis results for informed responses
- **Rule-Based Fallback**: Functions without LLM connectivity
- **LZA Expertise**: Specialized knowledge of LZA patterns
- **Session Management**: Proper resource cleanup

**Session Flow**:
```python
async def start(self, input_dir: str, analysis_results: Optional[Dict] = None):
    # 1. Load analysis data
    # 2. Initialize LLM connection
    # 3. Create context summary
    # 4. Show welcome message
    # 5. Start Q&A loop
```

#### Context Preparation

**Analysis Summary**:
```python
def _create_context_summary(self):
    self.context_summary = f"""
    LZA Analysis Context:
    - Total stacks analyzed: {stacks}
    - Resources changed: {resources}
    - IAM changes: {iam_changes}
    - Analysis appears to be an LZA upgrade based on version parameter changes
    """
```

#### Question Processing

**LLM Response System**:
```python
async def _get_llm_response(self, question: str) -> str:
    system_prompt = f"""You are an expert AWS cloud administrator assistant...
    Context: {self.context_summary}
    User question: {question}"""
    
    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=question)
    ]
    
    response = await self.llm_provider.generate(messages)
    return response.content
```

**Rule-Based Responses**:
- **IAM Guidance**: Detailed IAM change analysis
- **Risk Guidance**: Risk level interpretation
- **Deployment Guidance**: Safe deployment practices
- **Parameter Guidance**: SSM parameter change explanations

#### Specialized Knowledge Base

**LZA-Specific Patterns**:
- Version upgrade detection
- Common change patterns
- Risk interpretation in LZA context
- Deployment best practices
- Rollback procedures

#### Maintenance Notes
- **Knowledge Updates**: Regular updates for new LZA versions
- **Response Quality**: Continuous improvement of rule-based responses
- **Error Handling**: Graceful degradation when LLM unavailable
- **User Experience**: Enhanced interaction patterns

---

## Configuration Management

### Location: `config/` directory

Manages system configuration through YAML files and environment variables.

#### LLM Configuration (`config/llm_config.yaml`)

**Structure**:
```yaml
default_provider: ollama
max_retries: 3
retry_delay: 1.0

fallback_chain:
  - ollama
  - openai
  - anthropic

providers:
  ollama:
    provider: ollama
    model: "qwen3:30b-a3b"
    temperature: 0.1
    max_tokens: 4096
    timeout: 30
    base_url: "http://localhost:11434"
    enabled: true
```

**Key Features**:
- **Provider Configuration**: Settings for each LLM provider
- **Fallback Chains**: Automatic provider switching
- **Environment Variables**: API key integration
- **Model Parameters**: Temperature, token limits, timeouts

#### Resource Categorization (`config/resource_categorization.yaml`)

**Purpose**: Optional custom resource categorization rules

**Features**:
- **Service Patterns**: Regex patterns for resource types
- **Custom Mappings**: Direct resource type mappings
- **Category Extensions**: Add new categories without code changes

#### Configuration Loading

**ConfigLoader Class**:
```python
class ConfigLoader:
    @staticmethod
    def load_default_config() -> LLMConfigManager:
        config_path = Path(__file__).parent.parent / "config" / "llm_config.yaml"
        return LLMConfigManager.from_yaml_file(config_path)
```

#### Maintenance Notes
- **Validation**: Pydantic-based configuration validation
- **Environment Integration**: Support for environment variables
- **Backward Compatibility**: Graceful handling of missing config
- **Documentation**: Clear examples and comments in config files

---

## Utilities & Helpers

### File Management Utilities

**Location**: `src/parsers/file_utils.py`

**FileValidator**:
- Directory existence validation
- File type verification
- Content structure checking
- Warning generation for unusual patterns

**FileManager**:
- Output directory structure creation
- Multi-format serialization (JSON, YAML, HTML)
- File path sanitization
- Error handling for write operations

### Progress and UI Utilities

**Rich Console Integration**:
- Progress bars for long operations
- Color-coded output based on risk levels
- Structured panels for organized display
- Interactive prompts for user input

### Error Handling Utilities

**Centralized Error Handling**:
- Custom exception classes
- Error categorization and reporting
- Graceful degradation strategies
- Comprehensive logging integration

## Component Maintenance Guidelines

### Adding New Components

1. **Follow Patterns**: Use existing components as templates
2. **Async Support**: Implement async/await where appropriate
3. **Error Handling**: Include comprehensive error handling
4. **Testing**: Add unit tests for new functionality
5. **Documentation**: Update this guide with new components

### Updating Existing Components

1. **Backward Compatibility**: Maintain API compatibility
2. **Configuration Updates**: Update YAML schemas if needed
3. **Error Handling**: Enhance error scenarios
4. **Performance**: Monitor performance impacts
5. **Documentation**: Update relevant documentation

### Common Maintenance Tasks

1. **AWS Service Updates**: Update resource categorization patterns
2. **LLM Provider Updates**: Add new providers or update APIs
3. **Report Templates**: Enhance HTML templates and styling
4. **Risk Patterns**: Update risk detection rules
5. **Configuration**: Add new configuration options

This component guide provides the technical foundation needed to maintain and extend the LZA Diff Analyzer effectively. Each component is designed for modularity and extensibility, making it straightforward to add new capabilities while maintaining system reliability.