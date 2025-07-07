# LZA Diff Analyzer - System Architecture Documentation

## Executive Summary

The LZA Diff Analyzer is a comprehensive Python-based tool designed to analyze AWS Landing Zone Accelerator (LZA) CloudFormation diff logs for potential risks and operational impacts. Built with enterprise-grade requirements in mind, it provides both rule-based and AI-powered analysis capabilities to help cloud administrators make informed decisions about LZA upgrades.

## System Overview

### Purpose
The tool analyzes CloudFormation diff files generated during LZA upgrades to:
- Identify potential security, operational, and compliance risks
- Provide actionable recommendations for safe deployment
- Generate comprehensive reports
- Enable interactive Q&A sessions for deeper analysis

### Key Capabilities
- **Multi-LLM Support**: Integrates with local models (Ollama) and cloud APIs (OpenAI, Anthropic)
- **Rule-Based Analysis**: Comprehensive risk detection using predefined patterns
- **Interactive Sessions**: Natural language Q&A for detailed exploration
- **Reporting**: Professional reports for technical teams
- **Scalable Architecture**: Handles large enterprise LZA deployments (100+ stacks)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LZA Diff Analyzer                            │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │     CLI     │    │   WebUI     │    │  API Layer  │         │
│  │  Interface  │    │🔮 (Planned) │    │🔮 (Planned) │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │              │
│  ┌──────┴───────────────────┴───────────────────┴─────────┐    │
│  │              Application Core                          │    │
│  │                                                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │    │
│  │  │   Parser    │  │  Analysis   │  │  Formatter  │   │    │
│  │  │   Layer     │  │   Engine    │  │    Layer    │   │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │    │
│  │         │                 │                 │        │    │
│  │  ┌──────┴──────┐ ┌───────┴───────┐ ┌──────┴──────┐  │    │
│  │  │    File     │ │     Risk      │ │   Report    │  │    │
│  │  │ Management  │ │  Analyzers    │ │ Generators  │  │    │
│  │  │             │ │               │ │             │  │    │
│  │  │• Validation │ │• Security     │ │• Executive  │  │    │
│  │  │• Parsing    │ │• Network      │ │• Technical  │  │    │
│  │  │• Storage    │ │• Operational  │ │• Compliance │  │    │
│  │  └─────────────┘ │• Compliance   │ └─────────────┘  │    │
│  │                  └───────────────┘                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 LLM Integration Layer                   │  │
│  │                                                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │   Ollama    │  │   OpenAI    │  │  Anthropic  │    │  │
│  │  │  Provider   │  │  Provider   │  │  Provider   │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │            Provider Abstraction Layer               │  │  │
│  │  │• Unified Interface  • Error Handling  • Fallbacks  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   Data Layer                            │  │
│  │                                                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │ Configuration│ │    Models   │  │   Output    │    │  │
│  │  │   Manager    │  │   (Pydantic)│  │  Manager    │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

External Interfaces:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Diff      │    │   Config    │    │   Reports   │
│   Files     │───▶│   Files     │───▶│   Output    │
│ (.diff)     │    │ (.yaml)     │    │(.html/.json)│
└─────────────┘    └─────────────┘    └─────────────┘
```

## Component Architecture

### Component Interaction Overview

```
┌─── COMPONENT INTERACTION ARCHITECTURE ───────────────────────────────────────────┐
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          USER INTERFACE LAYER                              │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │ │
│  │  │       CLI       │    │   Interactive   │    │   Future Web    │         │ │
│  │  │   Interface     │◄──►│    Session      │    │       UI        │         │ │
│  │  │   (simple_main.py)     │    │  (simple_session.py)   │    │   🔮 (Planned)   │         │ │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘         │ │
│  │           │                       │                       │                │ │
│  │           ▼                       ▼                       ▼                │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                      ORCHESTRATION LAYER                                   │ │
│  │                                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │           COMPREHENSIVE ANALYSIS ENGINE                                 │ │ │
│  │  │                    (analysis_engine.py)                                │ │ │
│  │  │                                                                         │ │ │
│  │  │  ┌─ WORKFLOW COORDINATOR ─────────────────────────────────────────────┐ │ │ │
│  │  │  │                                                                     │ │ │ │
│  │  │  │  1. Initialize Analysis Session                                     │ │ │ │
│  │  │  │  2. Load and Validate Configuration                                 │ │ │ │
│  │  │  │  3. Coordinate Parallel Analysis Execution                          │ │ │ │
│  │  │  │  4. Aggregate and Combine Results                                   │ │ │ │
│  │  │  │  5. Generate Comprehensive Assessment                               │ │ │ │
│  │  │  │                                                                     │ │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────┘ │ │ │
│  │  │                                      │                                 │ │ │
│  │  │                                      ▼                                 │ │ │
│  │  │  ┌─ ANALYSIS COORDINATION ────────────────────────────────────────────┐ │ │ │
│  │  │  │                                                                     │ │ │ │
│  │  │  │  Rule-Based Analysis ◄────────┐   ┌────────► LLM Analysis          │ │ │ │
│  │  │  │  (Always Executed)            │   │          (Conditional)         │ │ │ │
│  │  │  │           │                   │   │                   │            │ │ │ │
│  │  │  │           ▼                   │   │                   ▼            │ │ │ │
│  │  │  │  ┌─ Risk Analyzers ─────┐     │   │     ┌─ LLM Providers ────┐     │ │ │ │
│  │  │  │  │ • SecurityAnalyzer    │     │   │     │ • Ollama           │     │ │ │ │
│  │  │  │  │ • NetworkAnalyzer     │ ──► │ ● │ ◄── │ • OpenAI           │     │ │ │ │
│  │  │  │  │ • OperationalAnalyzer │     │   │     │ • Anthropic        │     │ │ │ │
│  │  │  │  │ • ComplianceAnalyzer  │     │   │     │ • Fallback Chain   │     │ │ │ │
│  │  │  │  └───────────────────────┘     │   │     └────────────────────┘     │ │ │ │
│  │  │  │           │                   │   │                   │            │ │ │ │
│  │  │  │           ▼                   │   │                   ▼            │ │ │ │
│  │  │  │  ┌─ Result Aggregation ──────────────────────────────────────────┐ │ │ │ │
│  │  │  │  │                                                               │ │ │ │ │
│  │  │  │  │  • Combine Rule-Based Findings                                │ │ │ │ │
│  │  │  │  │  • Integrate LLM Insights                                     │ │ │ │ │
│  │  │  │  │  • Generate Combined Assessment                               │ │ │ │ │
│  │  │  │  │  • Calculate Confidence Scores                               │ │ │ │ │
│  │  │  │  │  • Create ComprehensiveAnalysisResult                         │ │ │ │ │
│  │  │  │  │                                                               │ │ │ │ │
│  │  │  │  └───────────────────────────────────────────────────────────────┘ │ │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         PROCESSING LAYERS                                   │ │
│  │                                                                             │ │
│  │  ┌─ DATA LAYER ─────────┐   ┌─ LLM LAYER ──────┐   ┌─ OUTPUT LAYER ─────┐   │ │
│  │  │                      │   │                  │   │                    │   │ │
│  │  │ • DiffParser         │   │ • ProviderFactory │   │ • ReportGenerator  │   │ │
│  │  │ • DataModels         │   │ • ConfigManager   │   │ • AdminFormatter   │   │ │
│  │  │ • FileManager        │   │ • ClientProviders │   │ • FileSerializer   │   │ │
│  │  │ • Validation         │   │ • FallbackChains  │   │ • HTMLTemplates    │   │ │
│  │  │                      │   │                  │   │                    │   │ │
│  │  └──────────────────────┘   └──────────────────┘   └────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Risk Analyzer Coordination

```
┌─── RISK ANALYZER COORDINATION PATTERNS ──────────────────────────────────────────┐
│                                                                                  │
│  COMPREHENSIVE ANALYSIS ENGINE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        analyze() Method                                 │    │
│  │                                                                         │    │
│  │  INPUT: DiffAnalysis (parsed CloudFormation changes)                   │    │
│  │  OUTPUT: ComprehensiveAnalysisResult                                    │    │
│  │                                                                         │    │
│  │  ┌─── STEP 1: ANALYZER INITIALIZATION ─────────────────────────────────┐ │    │
│  │  │                                                                     │ │    │
│  │  │  self.risk_analyzers = [                                            │ │    │
│  │  │      SecurityRiskAnalyzer(),                                        │ │    │
│  │  │      NetworkRiskAnalyzer(),                                         │ │    │
│  │  │      OperationalRiskAnalyzer(),                                     │ │    │
│  │  │      ComplianceRiskAnalyzer()                                       │ │    │
│  │  │  ]                                                                  │ │    │
│  │  │                                                                     │ │    │
│  │  │  Each analyzer implements BaseRiskAnalyzer interface:               │ │    │
│  │  │  • async def analyze(diff_analysis) -> List[RiskFinding]             │ │    │
│  │  │  • Specialized risk detection logic                                 │ │    │
│  │  │  • Risk level classification (LOW/MEDIUM/HIGH/CRITICAL)             │ │    │
│  │  │  • Actionable recommendations                                       │ │    │
│  │  │  • Rollback procedures                                              │ │    │
│  │  └─────────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─── STEP 2: PARALLEL RULE-BASED ANALYSIS ───────────────────────────┐ │    │
│  │  │                                                                     │ │    │
│  │  │  async def _perform_rule_based_analysis():                          │ │    │
│  │  │                                                                     │ │    │
│  │  │      SecurityRiskAnalyzer            NetworkRiskAnalyzer           │ │    │
│  │  │      ┌─────────────────────┐         ┌─────────────────────┐       │ │    │
│  │  │      │                     │         │                     │       │ │    │
│  │  │      │ • IAM Permission    │         │ • Transit Gateway   │       │ │    │
│  │  │      │   Changes           │         │   Route Changes     │       │ │    │
│  │  │      │ • KMS Key Policy    │ ──────► │ • VPC Configuration │ ◄──── │ │    │
│  │  │      │   Modifications     │         │   Updates           │       │ │    │
│  │  │      │ • Cross-Account     │         │ • Security Group    │       │ │    │
│  │  │      │   Trust Relations   │         │   Modifications     │       │ │    │
│  │  │      │ • Encryption        │         │ • Direct Connect    │       │ │    │
│  │  │      │   Settings          │         │   Changes           │       │ │    │
│  │  │      │                     │         │                     │       │ │    │
│  │  │      └─────────────────────┘         └─────────────────────┘       │ │    │
│  │  │               │                               │                     │ │    │
│  │  │               ▼                               ▼                     │ │    │
│  │  │      OperationalRiskAnalyzer         ComplianceRiskAnalyzer        │ │    │
│  │  │      ┌─────────────────────┐         ┌─────────────────────┐       │ │    │
│  │  │      │                     │         │                     │       │ │    │
│  │  │      │ • Resource          │         │ • SOC2 Type II      │       │ │    │
│  │  │      │   Deletion Impact   │         │   Requirements      │       │ │    │
│  │  │      │ • Workload          │ ──────► │ • PCI-DSS           │ ◄──── │ │    │
│  │  │      │   Dependencies      │         │   Compliance        │       │ │    │
│  │  │      │ • Data Loss         │         │ • GDPR Data         │       │ │    │
│  │  │      │   Prevention        │         │   Protection        │       │ │    │
│  │  │      │ • Scaling and       │         │ • HIPAA Security    │       │ │    │
│  │  │      │   Performance       │         │   Controls          │       │ │    │
│  │  │      │                     │         │                     │       │ │    │
│  │  │      └─────────────────────┘         └─────────────────────┘       │ │    │
│  │  │               │                               │                     │ │    │
│  │  │               ▼                               ▼                     │ │    │
│  │  │  ┌─── RESULT COLLECTION ─────────────────────────────────────────┐  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  findings = []                                                │  │ │    │
│  │  │  │  for analyzer in self.risk_analyzers:                        │  │ │    │
│  │  │  │      try:                                                     │  │ │    │
│  │  │  │          analyzer_findings = await analyzer.analyze(diff)    │  │ │    │
│  │  │  │          findings.extend(analyzer_findings)                  │  │ │    │
│  │  │  │      except Exception as e:                                  │  │ │    │
│  │  │  │          log_error(f"Analyzer {analyzer} failed: {e}")       │  │ │    │
│  │  │  │          continue  # Continue with other analyzers            │  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  return RuleBasedAnalysisResult(findings=findings)           │  │ │    │
│  │  │  └───────────────────────────────────────────────────────────────┘  │ │    │
│  │  └─────────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─── STEP 3: LLM ANALYSIS COORDINATION (if enabled) ─────────────────┐ │    │
│  │  │                                                                     │ │    │
│  │  │  async def _perform_llm_analysis():                                 │ │    │
│  │  │                                                                     │ │    │
│  │  │  ┌─ PROVIDER SELECTION ──────────────────────────────────────────┐  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  providers_to_try = []                                        │  │ │    │
│  │  │  │  if preferred_provider:                                       │  │ │    │
│  │  │  │      providers_to_try.append(preferred_provider_config)       │  │ │    │
│  │  │  │  providers_to_try.extend(fallback_configs)                    │  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  Order: [Primary] → [Secondary] → [Tertiary]                  │  │ │    │
│  │  │  │         ollama   → openai      → anthropic                    │  │ │    │
│  │  │  └───────────────────────────────────────────────────────────────┘  │ │    │
│  │  │                                      │                             │ │    │
│  │  │                                      ▼                             │ │    │
│  │  │  ┌─ CONTEXT PREPARATION ─────────────────────────────────────────┐  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  context_summary = self._create_changes_summary(diff_analysis) │  │ │    │
│  │  │  │  rule_findings_summary = self._summarize_findings(findings)   │  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  Combined Context:                                            │  │ │    │
│  │  │  │  • Stack count and resource changes                           │  │ │    │
│  │  │  │  • IAM modifications summary                                  │  │ │    │
│  │  │  │  • Resource category breakdown                                │  │ │    │
│  │  │  │  • Rule-based findings preview                                │  │ │    │
│  │  │  │  • LZA version upgrade context                                │  │ │    │
│  │  │  └───────────────────────────────────────────────────────────────┘  │ │    │
│  │  │                                      │                             │ │    │
│  │  │                                      ▼                             │ │    │
│  │  │  ┌─ SPECIALIZED PROMPTS (Parallel) ─────────────────────────────┐  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  await asyncio.gather(                                        │  │ │    │
│  │  │  │      self._llm_overall_assessment(context),                   │  │ │    │
│  │  │  │      self._llm_network_analysis(context),                     │  │ │    │
│  │  │  │      self._llm_security_analysis(context),                    │  │ │    │
│  │  │  │      self._llm_operational_analysis(context)                  │  │ │    │
│  │  │  │  )                                                            │  │ │    │
│  │  │  │                                                               │  │ │    │
│  │  │  │  Each prompt provides:                                        │  │ │    │
│  │  │  │  • Business context interpretation                            │  │ │    │
│  │  │  │  • Additional risk identification                             │  │ │    │
│  │  │  │  • Deployment recommendations                                 │  │ │    │
│  │  │  │  • Rollback strategies                                        │  │ │    │
│  │  │  └───────────────────────────────────────────────────────────────┘  │ │    │
│  │  └─────────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─── STEP 4: RESULT COMBINATION AND ASSESSMENT ─────────────────────┐ │    │
│  │  │                                                                     │ │    │
│  │  │  combined_result = ComprehensiveAnalysisResult(                     │ │    │
│  │  │      analysis_id=generate_uuid(),                                   │ │    │
│  │  │      timestamp=datetime.now(),                                      │ │    │
│  │  │      diff_analysis=diff_analysis,                                   │ │    │
│  │  │      rule_based_analysis=rule_findings,                             │ │    │
│  │  │      llm_analysis=llm_insights,                                     │ │    │
│  │  │      combined_assessment=self._create_combined_assessment(),        │ │    │
│  │  │      analysis_metadata=self._create_metadata()                      │ │    │
│  │  │  )                                                                  │ │    │
│  │  │                                                                     │ │    │
│  │  │  Key Combination Logic:                                             │ │    │
│  │  │  • Merge rule-based and LLM insights                               │ │    │
│  │  │  • Calculate overall risk level                                    │ │    │
│  │  │  • Prioritize findings by impact                                   │ │    │
│  │  │  • Generate actionable recommendations                             │ │    │
│  │  │  • Create executive summary                                        │ │    │
│  │  │  • Assess analysis confidence                                      │ │    │
│  │  └─────────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Command Line Interface (`src/cli/`)

**Purpose**: User-facing interface providing commands for analysis and interaction

**Key Components**:
- `simple_main.py`: Primary CLI entry point with Click-based commands
  - Comprehensive diff analysis with multiple output formats
  - Built-in interactive AI-powered Q&A session
  - Integrated report generation
  - Configuration management through YAML files
- `analysis_runner.py`: Core analysis workflow coordination

**Dependencies**: 
- Click (CLI framework)
- Rich (Terminal UI)
- Asyncio (Concurrent operations)

### 2. Data Models (`src/models/`)

**Purpose**: Type-safe data structures using Pydantic for validation and serialization

**Key Components**:
- `diff_models.py`: Core data models for CloudFormation changes
  - `StackDiff`: Represents changes in a single stack
  - `ResourceChange`: Individual resource modifications
  - `IAMStatementChange`: IAM policy changes
  - `DiffAnalysis`: Complete analysis results
  - `ComprehensiveAnalysisResult`: Combined rule-based and LLM analysis

**Key Features**:
- **Resource Categorization System**: Automatic classification of AWS resources by service patterns
- **Future-Proof Design**: No hardcoded resource types - automatically adapts to new AWS services
- **Flexible Configuration**: Optional YAML-based categorization rules
- **JSON Serialization**: Proper handling of datetime and enum serialization

### 3. Parsing Layer (`src/parsers/`)

**Purpose**: Extracts structured data from CloudFormation diff files

**Key Components**:
- `diff_parser.py`: Core parser for CloudFormation diff format
  - Template section parsing (description changes)
  - IAM statement changes extraction
  - Resource changes with property-level details
  - Account/region metadata extraction
- `file_utils.py`: File management utilities
  - Directory validation
  - Output structure creation
  - Multi-format serialization (JSON, YAML, HTML)

**Parsing Capabilities**:
- **Multi-Section Parsing**: Handles template, IAM, and resource sections
- **Property-Level Changes**: Detailed tracking of resource property modifications
- **Metadata Extraction**: Account IDs, regions, and stack names from filenames
- **Error Resilience**: Continues processing despite individual file parsing errors

### 4. Analysis Engine (`src/analyzers/`)

**Purpose**: Multi-layered risk analysis combining rule-based and AI-powered insights

#### Core Engine (`analysis_engine.py`)
- **Comprehensive Analysis**: Coordinates rule-based and LLM analysis
- **Provider Management**: Handles LLM fallback chains and error recovery
- **Prompt Engineering**: Specialized prompts for different analysis types
- **Result Combination**: Merges insights from multiple analysis methods

#### Risk Analyzers (`base.py`, `*_analyzer.py`)
- **Security Analyzer**: IAM permissions, encryption, access control risks
- **Network Analyzer**: Connectivity, routing, and network security impacts
- **Operational Analyzer**: Workload impact, data loss prevention, scaling considerations
- **Compliance Analyzer**: Regulatory framework impacts (SOC2, PCI-DSS, GDPR, etc.)

**Analysis Features**:
- **Risk Scoring**: LOW/MEDIUM/HIGH/CRITICAL classification
- **Impact Assessment**: Business and technical impact descriptions
- **Actionable Recommendations**: Specific mitigation steps
- **Rollback Procedures**: Detailed recovery instructions
- **Confidence Scoring**: Assessment reliability metrics

### 5. LLM Integration Layer (`src/llm/`)

**Purpose**: Unified interface for multiple LLM providers with robust error handling

### LLM Provider Selection and Fallback Sequence

```
┌─── LLM INTEGRATION SEQUENCE DIAGRAMS ────────────────────────────────────────────┐
│                                                                                  │
│  SEQUENCE 1: SUCCESSFUL LLM ANALYSIS WITH PRIMARY PROVIDER                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Analysis Engine              LLM Config Manager         Ollama Client  │    │
│  │       │                            │                          │         │    │
│  │       │ analyze()                  │                          │         │    │
│  │       ├─────────────────────────── ▶                          │         │    │
│  │       │                            │                          │         │    │
│  │       │ get_llm_config('ollama')   │                          │         │    │
│  │       ├─────────────────────────── ▶                          │         │    │
│  │       │                            │                          │         │    │
│  │       │ ◄─────────────────────────── LLMConfig(ollama)        │         │    │
│  │       │                            │                          │         │    │
│  │       │ create_provider(config)     │                          │         │    │
│  │       ├─────────────────────────── ▶                          │         │    │
│  │       │                            │                          │         │    │
│  │       │ ◄─────────────────────────── OllamaClient()           │         │    │
│  │       │                            │                          │         │    │
│  │       │ is_available()              │                          │         │    │
│  │       ├──────────────────────────────────────────────────────── ▶       │    │
│  │       │                            │                          │         │    │
│  │       │ ◄─────────────────────────────────────────────────────── True   │    │
│  │       │                            │                          │         │    │
│  │       │ generate(messages)          │                          │         │    │
│  │       ├──────────────────────────────────────────────────────── ▶       │    │
│  │       │                            │                          │         │    │
│  │       │                            │                          │ HTTP    │    │
│  │       │                            │                          │ POST    │    │
│  │       │                            │                          │ /api/   │    │
│  │       │                            │                          │ generate│    │
│  │       │                            │                          │ ─────── ▶    │
│  │       │                            │                          │         │ Ollama │
│  │       │                            │                          │         │ Service│
│  │       │                            │                          │ ◄─────── │    │
│  │       │                            │                          │ Response │    │
│  │       │ ◄─────────────────────────────────────────────────────── LLM     │    │
│  │       │                            │                          │ Response │    │
│  │       │                            │                          │         │    │
│  │       │ SUCCESS: Continue with      │                          │         │    │
│  │       │ LLM-enhanced analysis       │                          │         │    │
│  │       ▼                            │                          │         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  SEQUENCE 2: FALLBACK CHAIN EXECUTION DUE TO PRIMARY PROVIDER FAILURE          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Analysis Engine    Config Manager    Ollama Client    OpenAI Client    │    │
│  │       │                   │                │                 │          │    │
│  │       │ get_fallback_configs()             │                 │          │    │
│  │       ├──────────────────▶                 │                 │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ ◄────────────────── [ollama, openai, anthropic]      │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ Try Provider 1: Ollama             │                 │          │    │
│  │       ├─────────────────────────────────── ▶                 │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ is_available()     │                │                 │          │    │
│  │       ├─────────────────────────────────── ▶                 │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ ◄─────────────────────────────────── ConnectionError  │          │    │
│  │       │                   │                │ (Ollama down)    │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ Log: "Ollama unavailable, trying fallback"           │          │    │
│  │       │                   │                │                 │          │    │
│  │       │ Try Provider 2: OpenAI             │                 │          │    │
│  │       ├─────────────────────────────────────────────────────── ▶        │    │
│  │       │                   │                │                 │          │    │
│  │       │ is_available()     │                │                 │          │    │
│  │       ├─────────────────────────────────────────────────────── ▶        │    │
│  │       │                   │                │                 │          │    │
│  │       │ ◄─────────────────────────────────────────────────────── True   │    │
│  │       │                   │                │                 │          │    │
│  │       │ generate(messages) │                │                 │          │    │
│  │       ├─────────────────────────────────────────────────────── ▶        │    │
│  │       │                   │                │                 │          │    │
│  │       │                   │                │                 │ HTTPS   │    │
│  │       │                   │                │                 │ POST    │    │
│  │       │                   │                │                 │ OpenAI  │    │
│  │       │                   │                │                 │ API     │    │
│  │       │                   │                │                 │ ─────── ▶    │
│  │       │                   │                │                 │         │ OpenAI │
│  │       │                   │                │                 │ ◄─────── │ Service│
│  │       │                   │                │                 │ Response │    │
│  │       │ ◄─────────────────────────────────────────────────────── LLM     │    │
│  │       │                   │                │                 │ Response │    │
│  │       │                   │                │                 │          │    │
│  │       │ SUCCESS: Continue with fallback provider             │          │    │
│  │       ▼                   │                │                 │          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  SEQUENCE 3: COMPLETE LLM FAILURE - GRACEFUL DEGRADATION                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Analysis Engine         All LLM Providers         Rule-Based Analysis  │    │
│  │       │                        │                          │             │    │
│  │       │ Try all providers in fallback chain               │             │    │
│  │       ├───────────────────────▶                           │             │    │
│  │       │                        │                          │             │    │
│  │       │ ◄─────────────────────── All providers failed     │             │    │
│  │       │                        │ (network issues,         │             │    │
│  │       │                        │  API quotas exceeded,    │             │    │
│  │       │                        │  service unavailable)    │             │    │
│  │       │                        │                          │             │    │
│  │       │ Log: "LLM analysis failed, continuing with rule-based only"     │    │
│  │       │                        │                          │             │    │
│  │       │ continue_with_rule_based_analysis()               │             │    │
│  │       ├────────────────────────────────────────────────── ▶             │    │
│  │       │                        │                          │             │    │
│  │       │ ◄────────────────────────────────────────────────── Rule-Based │    │
│  │       │                        │                          │ Findings   │    │
│  │       │                        │                          │             │    │
│  │       │ create_analysis_result(rule_findings, llm_insights=None)        │    │
│  │       │                        │                          │             │    │
│  │       │ analysis_metadata.llm_enhancement = "FAILED"      │             │    │
│  │       │ analysis_metadata.confidence_level = "MEDIUM"     │             │    │
│  │       │                        │                          │             │    │
│  │       │ SUCCESS: Analysis completes with reduced confidence but full    │    │
│  │       │          rule-based assessment available          │             │    │
│  │       ▼                        │                          │             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### LLM Error Handling and Recovery Patterns

```
┌─── LLM ERROR HANDLING PATTERNS ──────────────────────────────────────────────────┐
│                                                                                  │
│  ERROR TYPE 1: CONNECTION AND TIMEOUT ERRORS                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  try:                                                                   │    │
│  │      response = await client.generate(                                 │    │
│  │          messages=messages,                                             │    │
│  │          timeout=aiohttp.ClientTimeout(total=30)                       │    │
│  │      )                                                                  │    │
│  │  except asyncio.TimeoutError:                                          │    │
│  │      logger.warning(f"LLM request timeout for {provider}")             │    │
│  │      raise LLMError(                                                   │    │
│  │          f"Request timeout for {provider}",                            │    │
│  │          provider=provider,                                             │    │
│  │          error_type=ErrorType.TIMEOUT                                  │    │
│  │      )                                                                  │    │
│  │  except aiohttp.ClientError as e:                                      │    │
│  │      logger.warning(f"LLM connection error for {provider}: {e}")       │    │
│  │      raise LLMError(                                                   │    │
│  │          f"Connection failed for {provider}",                          │    │
│  │          provider=provider,                                             │    │
│  │          error_type=ErrorType.CONNECTION                               │    │
│  │      )                                                                  │    │
│  │                                                                         │    │
│  │  RECOVERY ACTION: Try next provider in fallback chain                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ERROR TYPE 2: AUTHENTICATION AND AUTHORIZATION ERRORS                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  if response.status == 401:                                            │    │
│  │      logger.error(f"Authentication failed for {provider}")             │    │
│  │      raise LLMError(                                                   │    │
│  │          f"Invalid API key for {provider}",                            │    │
│  │          provider=provider,                                             │    │
│  │          error_type=ErrorType.AUTHENTICATION                           │    │
│  │      )                                                                  │    │
│  │  elif response.status == 403:                                          │    │
│  │      logger.error(f"Authorization failed for {provider}")              │    │
│  │      raise LLMError(                                                   │    │
│  │          f"Insufficient permissions for {provider}",                   │    │
│  │          provider=provider,                                             │    │
│  │          error_type=ErrorType.AUTHORIZATION                            │    │
│  │      )                                                                  │    │
│  │                                                                         │    │
│  │  RECOVERY ACTION: Skip this provider, try next in chain                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ERROR TYPE 3: RATE LIMITING AND QUOTA ERRORS                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  if response.status == 429:                                            │    │
│  │      retry_after = response.headers.get('Retry-After', '60')           │    │
│  │      logger.warning(f"Rate limited by {provider}, retry after {retry_after}s") │
│  │                                                                         │    │
│  │      if attempt < max_retries:                                          │    │
│  │          await asyncio.sleep(int(retry_after))                         │    │
│  │          return await self._retry_request(messages, attempt + 1)       │    │
│  │      else:                                                              │    │
│  │          raise LLMError(                                               │    │
│  │              f"Rate limit exceeded for {provider}",                    │    │
│  │              provider=provider,                                         │    │
│  │              error_type=ErrorType.RATE_LIMIT                           │    │
│  │          )                                                              │    │
│  │                                                                         │    │
│  │  RECOVERY ACTION: Exponential backoff retry, then fallback             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ERROR TYPE 4: MODEL AND CONTENT ERRORS                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  if response.status == 400:                                            │    │
│  │      error_data = await response.json()                                │    │
│  │      error_msg = error_data.get('error', {}).get('message', 'Unknown') │    │
│  │                                                                         │    │
│  │      if 'content filter' in error_msg.lower():                         │    │
│  │          logger.warning(f"Content filtered by {provider}")             │    │
│  │          # Try with sanitized prompt                                    │    │
│  │          sanitized_messages = self._sanitize_messages(messages)        │    │
│  │          return await self.generate(sanitized_messages)                │    │
│  │                                                                         │    │
│  │      elif 'model not found' in error_msg.lower():                      │    │
│  │          logger.error(f"Model not available on {provider}")            │    │
│  │          raise LLMError(                                               │    │
│  │              f"Model unavailable for {provider}",                      │    │
│  │              provider=provider,                                         │    │
│  │              error_type=ErrorType.MODEL_ERROR                          │    │
│  │          )                                                              │    │
│  │                                                                         │    │
│  │  RECOVERY ACTION: Sanitize content and retry, or try next provider     │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  COMPREHENSIVE ERROR RECOVERY FLOW                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  async def _perform_llm_analysis_with_recovery():                       │    │
│  │                                                                         │    │
│  │      providers_tried = []                                              │    │
│  │      last_error = None                                                 │    │
│  │                                                                         │    │
│  │      for provider_config in self.get_provider_chain():                 │    │
│  │          try:                                                           │    │
│  │              logger.info(f"Attempting LLM analysis with {provider}")   │    │
│  │              provider = self.factory.create_provider(provider_config)  │    │
│  │                                                                         │    │
│  │              if not provider.is_available():                           │    │
│  │                  providers_tried.append(f"{provider.name}:unavailable")│    │
│  │                  continue                                               │    │
│  │                                                                         │    │
│  │              result = await provider.generate(messages)                │    │
│  │              logger.info(f"LLM analysis successful with {provider}")   │    │
│  │              return result                                              │    │
│  │                                                                         │    │
│  │          except LLMError as e:                                         │    │
│  │              providers_tried.append(f"{provider.name}:{e.error_type}") │    │
│  │              last_error = e                                             │    │
│  │              logger.warning(f"Provider {provider} failed: {e}")        │    │
│  │              continue                                                   │    │
│  │                                                                         │    │
│  │      # All providers failed                                            │    │
│  │      logger.error(f"All LLM providers failed: {providers_tried}")      │    │
│  │      self.analysis_metadata.llm_provider_attempts = providers_tried    │    │
│  │      self.analysis_metadata.llm_enhancement = "FAILED"                 │    │
│  │      self.analysis_metadata.confidence_level = "MEDIUM"                │    │
│  │                                                                         │    │
│  │      return None  # Graceful degradation to rule-based only            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Key Components**:
- `base.py`: Abstract provider interface and factory pattern
- `config.py`: Configuration management with fallback chains
- `ollama_client.py`: Local model integration via Ollama

**LLM Features**:
- **Multi-Provider Support**: Unified interface with provider abstraction
  - ✅ **Ollama**: Fully implemented (`ollama_client.py`)
  - ✅ **OpenAI**: Fully implemented (requires API key)
  - ✅ **Anthropic**: Fully implemented (requires API key)
- **Fallback Chains**: Automatic provider switching on failures
- **Async Operations**: Non-blocking LLM calls with timeout handling
- **Configuration Management**: YAML-based provider settings
- **Error Recovery**: Graceful degradation to rule-based analysis
- **Caching & Optimization**: Skip comprehensive analysis when recent results exist

**Current Implementation Status**:
- **Ollama Integration**: Production ready with full error handling
- **OpenAI Integration**: Production ready (requires API key configuration)
- **Anthropic Integration**: Production ready (requires API key configuration)
- **Provider Factory**: Complete with unified interface pattern
- **Fallback System**: Implemented and tested across all providers

### 6. Reporting & Formatting (`src/reports/`, `src/formatters/`)

**Purpose**: Generate stakeholder-appropriate outputs

#### Report Generator (`report_generator.py`)
- **Executive Reports**: Business-focused summaries for decision makers
- **Technical Reports**: Detailed findings for engineering teams
- **Risk Matrix Reports**: Visual risk assessment matrices
- **Compliance Reports**: Regulatory impact assessments
- **HTML Generation**: Professional styling with Jinja2 templates

#### Admin-Friendly Formatter (`admin_friendly.py`)
- **Cloud Administrator Focus**: Simplified, actionable summaries
- **Risk Prioritization**: Key concerns requiring immediate attention
- **Action Checklists**: Immediate next steps
- **Context Explanation**: Why findings matter and what they mean

### 7. Interactive Session (`src/interactive/`)

**Purpose**: Natural language Q&A interface for detailed analysis exploration

**Key Components**:
- `simple_session.py`: Streamlined interactive session implementation

**Key Features**:
- **Context-Aware**: Uses analysis results to provide informed responses
- **Rule-Based Fallback**: Functions without LLM for basic guidance
- **Specialized Knowledge**: LZA-specific expertise and common patterns
- **Session Management**: Proper resource cleanup and error handling
- **Integrated Workflow**: Seamlessly transitions from analysis to interactive mode

## Data Flow Architecture

### Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          LZA Diff Analyzer - Complete Data Flow                │
│                                                                                 │
│  INPUT STAGE                PROCESSING STAGE                OUTPUT STAGE        │
│  ┌─────────────┐            ┌─────────────────┐             ┌───────────────┐  │
│  │   .diff     │            │                 │             │   Reports     │  │
│  │   Files     │───────────▶│  Analysis       │────────────▶│   & Outputs   │  │
│  │             │            │  Pipeline       │             │               │  │
│  └─────────────┘            └─────────────────┘             └───────────────┘  │
│  ┌─────────────┐            ┌─────────────────┐             ┌───────────────┐  │
│  │  Config     │            │                 │             │  Interactive  │  │
│  │  Files      │───────────▶│   LLM Layer     │────────────▶│   Sessions    │  │
│  │  (.yaml)    │            │                 │             │               │  │
│  └─────────────┘            └─────────────────┘             └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Input Processing Flow

```
┌─── INPUT VALIDATION & PARSING ──────────────────────────────────────────────────┐
│                                                                                  │
│  CloudFormation Diff Files (.diff)                                              │
│  ┌─────────────────────────────────────────────────┐                           │
│  │  AWSAccelerator-SecurityStack-145023093216.diff │                           │
│  │  AWSAccelerator-NetworkStack-238611950256.diff  │                           │
│  │  AWSAccelerator-IAMStack-504706990227.diff      │ ───┐                      │
│  │  ... (up to 100+ stack files)                   │    │                      │
│  └─────────────────────────────────────────────────┘    │                      │
│                                                         │                      │
│                                                         ▼                      │
│  ┌─── FILE VALIDATION (file_utils.py) ─────────────────────────────────────────┐ │
│  │  • Check file extensions (.diff required)                                   │ │
│  │  • Validate directory structure                                             │ │
│  │  • Verify file readability and size limits                                 │ │
│  │  • Extract metadata (account ID, region, stack name)                       │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── DIFF PARSER (diff_parser.py) ────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  TEMPLATE SECTION PARSING:                                                 │ │
│  │  ├─ Description Changes    → Version Detection (LZA 1.10.0 → 1.12.1)      │ │
│  │  ├─ Parameter Updates      → SSM Parameter Modifications                   │ │
│  │  └─ Metadata Extraction    → Stack Context Information                     │ │
│  │                                                                             │ │
│  │  IAM STATEMENT PARSING:                                                    │ │
│  │  ├─ Table Format Processing   │ + │ Resource │ Effect │ Action │ Principal │ │
│  │  ├─ Change Type Detection (ADD/MODIFY/DELETE)                              │ │
│  │  ├─ Policy Statement Extraction                                            │ │
│  │  └─ Cross-Account Role Analysis                                            │ │
│  │                                                                             │ │
│  │  RESOURCE SECTION PARSING:                                                 │ │
│  │  ├─ Resource Type Identification (AWS::IAM::Role, AWS::EC2::VPC, etc.)     │ │
│  │  ├─ Property-Level Change Detection                                        │ │
│  │  ├─ Resource Dependency Mapping                                            │ │
│  │  └─ Change Impact Assessment                                               │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── DATA MODEL CREATION (diff_models.py) ────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  PYDANTIC MODEL INSTANTIATION:                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│  │  │  DiffAnalysis                                                       │   │ │
│  │  │  ├─ timestamp: datetime                                             │   │ │
│  │  │  ├─ stack_diffs: List[StackDiff]                                    │   │ │
│  │  │  ├─ total_stacks: int                                               │   │ │
│  │  │  ├─ total_resources_changed: int                                    │   │ │
│  │  │  └─ total_iam_changes: int                                          │   │ │
│  │  │                                                                     │   │ │
│  │  │    StackDiff                                                        │   │ │
│  │  │    ├─ stack_name: str                                               │   │ │
│  │  │    ├─ resource_changes: List[ResourceChange]                        │   │ │
│  │  │    ├─ iam_statement_changes: List[IAMStatementChange]               │   │ │
│  │  │    ├─ account_id: Optional[str]                                     │   │ │
│  │  │    └─ region: Optional[str]                                         │   │ │
│  │  │                                                                     │   │ │
│  │  │      ResourceChange                                                 │   │ │
│  │  │      ├─ logical_id: str                                             │   │ │
│  │  │      ├─ resource_type: str                                          │   │ │
│  │  │      ├─ change_type: ChangeType                                     │   │ │
│  │  │      ├─ property_changes: List[PropertyChange]                      │   │ │
│  │  │      └─ parsed_resource_category: ResourceCategory (auto-assigned)   │   │ │
│  │  └─────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                             │ │
│  │  AUTOMATIC RESOURCE CATEGORIZATION:                                        │ │
│  │  ├─ Service Pattern Matching (AWS::IAM::* → IAM_RESOURCES)                 │ │
│  │  ├─ Security Classification (KMS, SecretsManager → SECURITY_RESOURCES)     │ │
│  │  ├─ Network Resource Detection (VPC, TGW → NETWORK_RESOURCES)              │ │
│  │  └─ Future-Proof Pattern System (adapts to new AWS services)               │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Comprehensive Analysis Processing Flow

```
┌─── ANALYSIS ENGINE COORDINATION ─────────────────────────────────────────────────┐
│                                                                                  │
│  DiffAnalysis (Parsed & Validated Data)                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  • 74 CloudFormation Stacks                                            │    │
│  │  • 225 Resource Changes                                                 │    │
│  │  │  ├─ 156 IAM Resources                                                │    │
│  │  │  ├─ 34 Network Resources                                             │    │
│  │  │  ├─ 23 Security Resources                                            │    │
│  │  │  └─ 12 Other Resources                                               │    │
│  │  • 462 IAM Statement Changes                                            │    │
│  │  │  ├─ 258 Policy Modifications                                         │    │
│  │  │  ├─ 134 Role Updates                                                 │    │
│  │  │  └─ 70 Trust Relationship Changes                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── COMPREHENSIVE ANALYSIS ENGINE (analysis_engine.py) ──────────────────────┐ │
│  │                                                                             │ │
│  │  ┌─── PARALLEL ANALYSIS EXECUTION ─────────────────────────────────────────┐ │ │
│  │  │                                                                         │ │ │
│  │  │  RULE-BASED ANALYSIS (Always Executed)                                 │ │ │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │ │ │
│  │  │  │  Security Risk  │    │  Network Risk   │    │ Operational Risk│     │ │ │
│  │  │  │    Analyzer     │    │    Analyzer     │    │    Analyzer     │     │ │ │
│  │  │  │                 │    │                 │    │                 │     │ │ │
│  │  │  │ • IAM Changes   │    │ • TGW Routes    │    │ • Data Loss     │     │ │ │
│  │  │  │ • KMS Policies  │    │ • VPC Configs   │    │ • Dependencies  │     │ │ │
│  │  │  │ • Access Rights │    │ • Cross-Account │    │ • Workload Impact│     │ │ │
│  │  │  │ • Encryption    │    │ • Direct Connect│    │ • Scaling       │     │ │ │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     │ │ │
│  │  │           │                       │                       │            │ │ │
│  │  │           ▼                       ▼                       ▼            │ │ │
│  │  │  ┌─────────────────┐                                                   │ │ │
│  │  │  │ Compliance Risk │     ◄────── Risk Finding Aggregation ──────────► │ │ │
│  │  │  │    Analyzer     │                                                   │ │ │
│  │  │  │                 │     Each analyzer returns:                       │ │ │
│  │  │  │ • SOC2 Impact   │     • List[RiskFinding]                          │ │ │
│  │  │  │ • PCI-DSS       │     • Risk Level (LOW/MEDIUM/HIGH/CRITICAL)       │ │ │
│  │  │  │ • GDPR          │     • Recommendations                             │ │ │
│  │  │  │ • HIPAA         │     • Rollback Steps                              │ │ │
│  │  │  │ • ISO27001      │     • Confidence Score                            │ │ │
│  │  │  └─────────────────┘                                                   │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                      │                                      │ │
│  │                                      ▼                                      │ │
│  │  ┌─── LLM ANALYSIS (Conditional) ──────────────────────────────────────────┐ │ │
│  │  │                                                                         │ │ │
│  │  │  LLM PROVIDER SELECTION & FALLBACK CHAIN                               │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────│ │ │
│  │  │  │  1. Primary Provider (from config: ollama/openai/anthropic)        │ │ │
│  │  │  │     ├─ Check availability (health check)                            │ │ │
│  │  │  │     ├─ Verify configuration (API keys, endpoints)                   │ │ │
│  │  │  │     └─ Test connectivity                                            │ │ │
│  │  │  │                                                                     │ │ │
│  │  │  │  2. Fallback Chain Execution                                        │ │ │
│  │  │  │     ├─ If primary fails → try secondary provider                    │ │ │
│  │  │  │     ├─ If secondary fails → try tertiary provider                   │ │ │
│  │  │  │     └─ If all fail → continue with rule-based analysis only         │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────│ │ │
│  │  │                                      │                                 │ │ │
│  │  │                                      ▼                                 │ │ │
│  │  │  CONTEXT PREPARATION & PROMPT ENGINEERING                              │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────│ │ │
│  │  │  │  Context Summary Generation:                                        │ │ │
│  │  │  │  • Change statistics and categorization                             │ │ │
│  │  │  │  • Rule-based findings summary                                      │ │ │
│  │  │  │  • Risk level distributions                                         │ │ │
│  │  │  │  • LZA version upgrade context                                      │ │ │
│  │  │  │                                                                     │ │ │
│  │  │  │  Specialized Prompts (Parallel Execution):                          │ │ │
│  │  │  │  ├─ Overall Assessment → Enterprise-wide impact analysis            │ │ │
│  │  │  │  ├─ Network Impact → Hub-spoke, TGW, Direct Connect analysis        │ │ │
│  │  │  │  ├─ Security Impact → Access control, encryption analysis           │ │ │
│  │  │  │  └─ Operational Readiness → Deployment guidance, rollback plans     │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────│ │ │
│  │  │                                      │                                 │ │ │
│  │  │                                      ▼                                 │ │ │
│  │  │  LLM RESPONSE PROCESSING & INTEGRATION                                 │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────│ │ │
│  │  │  │  • Parse and validate LLM responses                                 │ │ │
│  │  │  │  • Extract actionable insights and recommendations                  │ │ │
│  │  │  │  • Identify additional risks not caught by rule-based analysis     │ │ │
│  │  │  │  • Generate business context and impact explanations               │ │ │
│  │  │  │  • Create deployment and rollback guidance                          │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────│ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                      │                                      │ │
│  │                                      ▼                                      │ │
│  │  ┌─── ANALYSIS RESULT COMBINATION ──────────────────────────────────────────┐ │ │
│  │  │                                                                         │ │ │
│  │  │  ComprehensiveAnalysisResult Creation:                                  │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────│ │ │
│  │  │  │  Rule-Based Findings:                                               │ │ │
│  │  │  │  ├─ Security: 45 findings (3 CRITICAL, 12 HIGH, 30 MEDIUM)         │ │ │
│  │  │  │  ├─ Network: 23 findings (1 HIGH, 22 MEDIUM)                       │ │ │
│  │  │  │  ├─ Operational: 34 findings (2 HIGH, 32 MEDIUM)                   │ │ │
│  │  │  │  └─ Compliance: 12 findings (12 MEDIUM)                            │ │ │
│  │  │  │                                                                     │ │ │
│  │  │  │  LLM Insights (if available):                                       │ │ │
│  │  │  │  ├─ Overall Assessment: "Standard LZA upgrade pattern"              │ │ │
│  │  │  │  ├─ Network Impact: "Hub-spoke connectivity maintained"             │ │ │
│  │  │  │  ├─ Security Impact: "Cross-account roles require validation"       │ │ │
│  │  │  │  └─ Operational Readiness: "Test IAM in non-prod first"             │ │ │
│  │  │  │                                                                     │ │ │
│  │  │  │  Combined Assessment:                                               │ │ │
│  │  │  │  ├─ Overall Risk Level: MEDIUM                                      │ │ │
│  │  │  │  ├─ Key Concerns: IAM permission changes, cross-account access      │ │ │
│  │  │  │  ├─ Immediate Actions: Test in non-prod, validate IAM changes       │ │ │
│  │  │  │  └─ Analysis Confidence: HIGH (rule-based + LLM validation)         │ │ │
│  │  │  │                                                                     │ │ │
│  │  │  │  Metadata & Statistics:                                             │ │ │
│  │  │  │  ├─ Analysis Duration: 45.2 seconds                                 │ │ │
│  │  │  │  ├─ LLM Provider Used: ollama (qwen3:30b-a3b)                       │ │ │
│  │  │  │  ├─ Rule-Based Findings: 114 total                                  │ │ │
│  │  │  │  └─ LLM Enhancement: SUCCESS                                        │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────────│ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Enhanced Output Generation Flow

```
┌─── OUTPUT GENERATION & FORMATTING ───────────────────────────────────────────────┐
│                                                                                  │
│  ComprehensiveAnalysisResult (Complete Analysis Data)                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  • Analysis Metadata (timestamp, duration, confidence)                 │    │
│  │  • Rule-Based Findings (114 total across 4 risk categories)            │    │
│  │  • LLM Insights (4 specialized assessments)                            │    │
│  │  • Combined Assessment (overall risk level, key concerns)              │    │
│  │  • Statistics (stacks analyzed, resources changed, IAM changes)        │    │
│  │  • Recommendations (immediate actions, testing guidance)               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── OUTPUT FORMAT SELECTION ──────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  User-Specified Format (CLI Options)                                       │ │
│  │  ├─ --format json    → Machine-readable output                             │ │
│  │  ├─ --format yaml    → Human-readable structured output                    │ │
│  │  ├─ --format html    → Basic HTML output                                   │ │
│  │  ├─ --generate-reports → Comprehensive enterprise reports                  │ │
│  │  └─ Default: admin-friendly console output                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── PARALLEL OUTPUT GENERATION ───────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │ │
│  │  │  JSON/YAML      │    │ Admin-Friendly  │    │  Interactive    │         │ │
│  │  │ Serialization   │    │    Summary      │    │   Session       │         │ │
│  │  │ (file_utils.py) │    │(admin_friendly) │    │  (simple_session.py)   │         │ │
│  │  │                 │    │                 │    │                 │         │ │
│  │  │ • Datetime      │    │ • Executive     │    │ • Context-Aware │         │ │
│  │  │   Handling      │    │   Summary       │    │   Q&A           │         │ │
│  │  │ • Enum          │    │ • Key Concerns  │    │ • LLM-Powered   │         │ │
│  │  │   Serialization │    │ • Action Items  │    │   Responses     │         │ │
│  │  │ • Custom        │    │ • LZA Context   │    │ • Rule-Based    │         │ │
│  │  │   Encoders      │    │ • Risk Priority │    │   Fallback      │         │ │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘         │ │
│  │           │                       │                       │                │ │
│  │           ▼                       ▼                       ▼                │ │
│  │  ┌─── ENTERPRISE REPORTS (report_generator.py) ─────────────────────────────┐ │ │
│  │  │                                                                         │ │ │
│  │  │  HTML Report Generation with Jinja2 Templates:                         │ │ │
│  │  │                                                                         │ │ │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │ │ │
│  │  │  │   Executive     │    │    Technical    │    │   Risk Matrix   │     │ │ │
│  │  │  │    Summary      │    │     Report      │    │     Report      │     │ │ │
│  │  │  │                 │    │                 │    │                 │     │ │ │
│  │  │  │ Target: C-Level │    │ Target: DevOps  │    │ Target: SecOps  │     │ │ │
│  │  │  │ • Business      │    │ • Detailed      │    │ • Visual Risk   │     │ │ │
│  │  │  │   Impact        │    │   Findings      │    │   Assessment    │     │ │ │
│  │  │  │ • High-Level    │    │ • Technical     │    │ • Compliance    │     │ │ │
│  │  │  │   Risks         │    │   Details       │    │   Framework     │     │ │ │
│  │  │  │ • Go/No-Go      │    │ • Code Changes  │    │   Mapping       │     │ │ │
│  │  │  │   Decision      │    │ • Rollback      │    │ • Risk Matrix   │     │ │ │
│  │  │  │ • Budget Impact │    │   Procedures    │    │   Visualization │     │ │ │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     │ │ │
│  │  │           │                       │                       │            │ │ │
│  │  │           ▼                       ▼                       ▼            │ │ │
│  │  │  ┌─────────────────┐                                                   │ │ │
│  │  │  │   Compliance    │    ◄────── Professional HTML Styling ──────────► │ │ │
│  │  │  │     Report      │                                                   │ │ │
│  │  │  │                 │    • Corporate CSS themes                         │ │ │
│  │  │  │ Target: Audit   │    • Responsive design                            │ │ │
│  │  │  │ • SOC2 Impact   │    • Print-friendly layouts                       │ │ │
│  │  │  │ • PCI-DSS       │    • Auto-escaping for security                   │ │ │
│  │  │  │ • GDPR          │    • Professional branding                        │ │ │
│  │  │  │ • HIPAA         │    • Interactive elements (future)                │ │ │
│  │  │  │ • ISO27001      │    • Export capabilities                          │ │ │
│  │  │  └─────────────────┘                                                   │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─── OUTPUT DELIVERY ───────────────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  File System Output:                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────│ │
│  │  │  output/                                                                │ │
│  │  │  ├── analysis/                                                          │ │
│  │  │  │   ├── diff_analysis.json                 (Machine processing)       │ │
│  │  │  │   ├── comprehensive_analysis.json        (Complete results)         │ │
│  │  │  │   └── analysis_summary.yaml               (Human readable)          │ │
│  │  │  │                                                                     │ │
│  │  │  ├── reports/                                                           │ │
│  │  │  │   ├── executive_summary.html              (C-Level audience)        │ │
│  │  │  │   ├── technical_report.html               (Engineering teams)       │ │
│  │  │  │   ├── risk_matrix.html                    (Security teams)          │ │
│  │  │  │   ├── compliance_report.html              (Audit teams)             │ │
│  │  │  │   └── full_report.html                    (Complete analysis)       │ │
│  │  │  │                                                                     │ │
│  │  │  ├── logs/                                                             │ │
│  │  │  │   ├── analysis.log                        (Process logging)         │ │
│  │  │  │   └── llm_interactions.log                (LLM request/response)    │ │
│  │  │  │                                                                     │ │
│  │  │  └── temp/                                                             │ │
│  │  │      └── intermediate_results/               (Debug & troubleshooting) │ │
│  │  └─────────────────────────────────────────────────────────────────────────│ │
│  │                                                                             │ │
│  │  Console Output (Real-time):                                               │ │
│  │  ├─ Rich-formatted progress bars and status updates                        │ │
│  │  ├─ Color-coded risk level indicators                                      │ │
│  │  ├─ Executive summary with immediate action items                          │ │
│  │  └─ Interactive prompts for session continuation                           │ │
│  │                                                                             │ │
│  │  Interactive Session (Optional):                                           │ │
│  │  ├─ Natural language Q&A interface                                         │ │
│  │  ├─ Context-aware responses using analysis results                         │ │
│  │  ├─ LLM-powered or rule-based fallback responses                           │ │
│  │  └─ Session transcripts saved for reference                                │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Input Validation
- **File Type Validation**: Only processes .diff files
- **Content Sanitization**: Prevents malicious input injection
- **Path Validation**: Ensures file paths are within expected directories
- **Size Limits**: Protects against resource exhaustion

### LLM Security
- **API Key Management**: Environment variable-based configuration
- **Request Sanitization**: Prevents prompt injection attacks
- **Rate Limiting**: Configurable timeouts and retry policies
- **Error Isolation**: LLM failures don't compromise rule-based analysis

### Output Security
- **Template Sanitization**: Jinja2 auto-escaping for HTML reports
- **Path Traversal Prevention**: Validates output file paths
- **Configuration Validation**: YAML parsing with safe loaders

## Performance Characteristics

### Scalability
- **Large Deployments**: Tested with 74 stacks, 225 resources, 462 IAM changes
- **Memory Efficiency**: Streaming parsing for large diff files
- **Concurrent Processing**: Async/await architecture for LLM calls
- **Incremental Analysis**: Can process individual stacks independently

### Performance Optimizations
- **Provider Fallback**: Minimizes LLM call failures
- **Caching**: Configuration caching to reduce file I/O
- **Batch Processing**: Groups similar analysis operations
- **Error Recovery**: Continues processing despite individual failures

## Configuration Management

### LLM Configuration (`config/llm_config.yaml`)
```yaml
default_provider: ollama
fallback_chain: [ollama, openai, anthropic]
providers:
  ollama:
    model: "qwen3:30b-a3b"  # Current production model
    temperature: 0.1
    max_tokens: 12288
  # Additional provider configurations...
```

### Resource Categorization (Optional)
- **Service Patterns**: Regex-based resource classification
- **Custom Mappings**: Override default categorizations
- **Extensible**: Add new categories without code changes

## Error Handling & Resilience

### Graceful Degradation
- **LLM Unavailable**: Falls back to rule-based analysis
- **Parsing Errors**: Continues with remaining files
- **Configuration Issues**: Uses sensible defaults
- **Network Failures**: Implements retry logic with exponential backoff

### Error Recovery
- **Provider Failures**: Automatic fallback to next LLM provider
- **Partial Analysis**: Returns available results even with some failures
- **Resource Cleanup**: Ensures proper cleanup of async resources
- **Detailed Logging**: Comprehensive error reporting for debugging

## Extension Points

### Adding New Analyzers
1. Inherit from `BaseRiskAnalyzer`
2. Implement analysis logic
3. Register with `RiskAnalysisEngine`

### Supporting New LLM Providers
1. Inherit from `BaseLLMProvider`
2. Implement provider-specific communication
3. Add configuration schema
4. Register with `LLMProviderFactory`

### Custom Report Formats
1. Create new Jinja2 templates
2. Add generation methods to `EnterpriseReportGenerator`
3. Update CLI options

### New Resource Types
- **Automatic Support**: Uses service pattern matching
- **Custom Categories**: Add patterns to configuration
- **No Code Changes**: Configuration-driven categorization

## Dependencies & Technology Stack

### Core Dependencies
- **Python 3.10+**: Modern Python features and type hints
- **Pydantic 2.0+**: Data validation and serialization
- **Click 8.1+**: Command-line interface framework
- **Rich 13.0+**: Terminal UI and progress indication
- **Jinja2 3.1+**: Template engine for report generation
- **PyYAML 6.0+**: Configuration file parsing
- **aiohttp 3.8+**: Async HTTP client for LLM APIs

### Optional Dependencies
- **Ollama SDK**: Local LLM integration
- **OpenAI SDK**: Cloud LLM integration
- **Anthropic SDK**: Claude API integration

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **mypy**: Static type checking
- **black**: Code formatting
- **isort**: Import sorting

## Deployment Considerations

### Environment Requirements
- **Python 3.10+**: Required for modern async features
- **Memory**: Minimum 2GB RAM for large analyses
- **Storage**: Configurable output directory
- **Network**: Optional for cloud LLM providers

### Installation Options
- **UV Package Manager**: Recommended for fast dependency resolution
- **Standard pip**: Alternative installation method
- **Development Setup**: Additional tools for code contribution

### Configuration Best Practices
- **Environment Variables**: API keys and sensitive configuration
- **YAML Files**: Non-sensitive configuration management
- **Default Fallbacks**: Ensure functionality without configuration
- **Validation**: Comprehensive configuration validation

This architecture provides a robust, scalable foundation for analyzing LZA deployments while maintaining flexibility for future enhancements and enterprise requirements.