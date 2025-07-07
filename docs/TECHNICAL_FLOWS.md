# LZA Diff Analyzer - Technical Flow Documentation

## Overview

This document provides detailed technical workflow diagrams and flowcharts for the LZA Diff Analyzer's internal processes. These diagrams complement the architecture documentation by showing step-by-step technical flows, decision points, and data transformations.

## Table of Contents

1. [Risk Analysis Workflows](#risk-analysis-workflows)
2. [Report Generation Pipeline](#report-generation-pipeline)
3. [Configuration Management Flow](#configuration-management-flow)
4. [Error Handling and Recovery](#error-handling-and-recovery)
5. [Interactive Session Management](#interactive-session-management)
6. [Parsing Pipeline Details](#parsing-pipeline-details)
7. [Resource Categorization System](#resource-categorization-system)
8. [Analysis Result Combination](#analysis-result-combination)

---

## Risk Analysis Workflows

### Multi-Analyzer Risk Assessment Flow

```
┌─── RISK ANALYSIS WORKFLOW ───────────────────────────────────────────────────────┐
│                                                                                  │
│  PHASE 1: ANALYZER INITIALIZATION & PREPARATION                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  ComprehensiveAnalysisEngine.analyze(diff_analysis)                     │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ ANALYZER INSTANTIATION ──────────────────────────────────────────┐  │    │
│  │  │                                                                   │  │    │
│  │  │  risk_analyzers = [                                               │  │    │
│  │  │      SecurityRiskAnalyzer(                                        │  │    │
│  │  │          high_risk_actions=["iam:*", "sts:AssumeRole", ...],      │  │    │
│  │  │          critical_resources=["AWS::IAM::Role", "AWS::KMS::Key"]    │  │    │
│  │  │      ),                                                            │  │    │
│  │  │      NetworkRiskAnalyzer(                                          │  │    │
│  │  │          network_services=["TGW", "VPC", "DirectConnect"],         │  │    │
│  │  │          routing_patterns=["hub-spoke", "transit-gateway"]         │  │    │
│  │  │      ),                                                            │  │    │
│  │  │      OperationalRiskAnalyzer(                                      │  │    │
│  │  │          data_services=["RDS", "DynamoDB", "S3"],                  │  │    │
│  │  │          workload_dependencies=["Lambda", "ECS", "EC2"]            │  │    │
│  │  │      ),                                                            │  │    │
│  │  │      ComplianceRiskAnalyzer(                                       │  │    │
│  │  │          frameworks=["SOC2", "PCI-DSS", "GDPR", "HIPAA"]           │  │    │
│  │  │      )                                                             │  │    │
│  │  │  ]                                                                 │  │    │
│  │  └───────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 2: PARALLEL ANALYSIS EXECUTION                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  async def _perform_rule_based_analysis(diff_analysis):                 │    │
│  │                                                                         │    │
│  │      SecurityRiskAnalyzer                                               │    │
│  │      ┌─────────────────────────────────────────────────────────────┐   │    │
│  │      │                                                             │   │    │
│  │      │  INPUT: DiffAnalysis                                        │   │    │
│  │      │  ├─ 74 stacks                                               │   │    │
│  │      │  ├─ 225 resource changes                                    │   │    │
│  │      │  └─ 462 IAM statement changes                               │   │    │
│  │      │                                                             │   │    │
│  │      │  PROCESSING STEPS:                                          │   │    │
│  │      │  1. Filter IAM-related changes                              │   │    │
│  │      │     ├─ Resource type: AWS::IAM::*                           │   │    │
│  │      │     ├─ IAM statement modifications                          │   │    │
│  │      │     └─ Trust relationship changes                           │   │    │
│  │      │                                                             │   │    │
│  │      │  2. Risk Pattern Matching                                   │   │    │
│  │      │     for change in iam_changes:                              │   │    │
│  │      │         if self._is_high_risk_action(change.action):        │   │    │
│  │      │             risk_level = HIGH                               │   │    │
│  │      │         elif self._is_cross_account_change(change):         │   │    │
│  │      │             risk_level = MEDIUM                             │   │    │
│  │      │         else:                                               │   │    │
│  │      │             risk_level = LOW                                │   │    │
│  │      │                                                             │   │    │
│  │      │  3. Generate Risk Findings                                  │   │    │
│  │      │     findings.append(RiskFinding(                            │   │    │
│  │      │         finding_id=generate_uuid(),                         │   │    │
│  │      │         title="High-Risk IAM Permission Change",            │   │    │
│  │      │         risk_level=risk_level,                              │   │    │
│  │      │         recommendations=[...],                              │   │    │
│  │      │         rollback_steps=[...]                                │   │    │
│  │      │     ))                                                      │   │    │
│  │      │                                                             │   │    │
│  │      │  OUTPUT: List[RiskFinding] (45 security findings)          │   │    │
│  │      └─────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │      NetworkRiskAnalyzer                                               │    │
│  │      ┌─────────────────────────────────────────────────────────────┐   │    │
│  │      │                                                             │   │    │
│  │      │  PROCESSING STEPS:                                          │   │    │
│  │      │  1. Identify Network Resources                              │   │    │
│  │      │     ├─ AWS::EC2::VPC, AWS::EC2::Subnet                      │   │    │
│  │      │     ├─ AWS::EC2::TransitGateway*                            │   │    │
│  │      │     ├─ AWS::DirectConnect::*                                │   │    │
│  │      │     └─ AWS::EC2::SecurityGroup                              │   │    │
│  │      │                                                             │   │    │
│  │      │  2. Analyze Connectivity Impact                             │   │    │
│  │      │     for change in network_changes:                          │   │    │
│  │      │         if "route" in change.property_changes:              │   │    │
│  │      │             # Route table modifications                     │   │    │
│  │      │             analyze_routing_impact(change)                  │   │    │
│  │      │         elif "security_group_rules" in change:              │   │    │
│  │      │             # Security group rule changes                   │   │    │
│  │      │             analyze_access_impact(change)                   │   │    │
│  │      │                                                             │   │    │
│  │      │  3. Hub-Spoke Architecture Analysis                         │   │    │
│  │      │     if transit_gateway_changes:                             │   │    │
│  │      │         assess_hub_spoke_connectivity()                     │   │    │
│  │      │         check_cross_account_routing()                       │   │    │
│  │      │                                                             │   │    │
│  │      │  OUTPUT: List[RiskFinding] (23 network findings)           │   │    │
│  │      └─────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │      OperationalRiskAnalyzer                                           │    │
│  │      ┌─────────────────────────────────────────────────────────────┐   │    │
│  │      │                                                             │   │    │
│  │      │  PROCESSING STEPS:                                          │   │    │
│  │      │  1. Resource Deletion Analysis                              │   │    │
│  │      │     for change in resource_changes:                         │   │    │
│  │      │         if change.change_type == DELETE:                    │   │    │
│  │      │             analyze_deletion_impact(change)                 │   │    │
│  │      │             check_data_loss_potential(change)               │   │    │
│  │      │                                                             │   │    │
│  │      │  2. Workload Dependency Assessment                          │   │    │
│  │      │     dependency_graph = build_resource_dependencies()        │   │    │
│  │      │     for change in changes:                                  │   │    │
│  │      │         affected_resources = find_dependents(change)        │   │    │
│  │      │         assess_cascading_impact(affected_resources)         │   │    │
│  │      │                                                             │   │    │
│  │      │  3. Performance and Scaling Impact                          │   │    │
│  │      │     if autoscaling_changes or capacity_changes:             │   │    │
│  │      │         analyze_performance_impact()                        │   │    │
│  │      │                                                             │   │    │
│  │      │  OUTPUT: List[RiskFinding] (34 operational findings)       │   │    │
│  │      └─────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │      ComplianceRiskAnalyzer                                            │    │
│  │      ┌─────────────────────────────────────────────────────────────┐   │    │
│  │      │                                                             │   │    │
│  │      │  PROCESSING STEPS:                                          │   │    │
│  │      │  1. Compliance Framework Mapping                            │   │    │
│  │      │     compliance_requirements = {                             │   │    │
│  │      │         "SOC2": ["access_controls", "encryption", "audit"], │   │    │
│  │      │         "PCI-DSS": ["data_protection", "network_security"], │   │    │
│  │      │         "GDPR": ["data_privacy", "retention_policies"],     │   │    │
│  │      │         "HIPAA": ["phi_protection", "access_logging"]       │   │    │
│  │      │     }                                                       │   │    │
│  │      │                                                             │   │    │
│  │      │  2. Change Impact Assessment                                │   │    │
│  │      │     for framework, requirements in frameworks.items():      │   │    │
│  │      │         for requirement in requirements:                    │   │    │
│  │      │             if affects_compliance_requirement(              │   │    │
│  │      │                 changes, framework, requirement             │   │    │
│  │      │             ):                                              │   │    │
│  │      │                 create_compliance_finding(                  │   │    │
│  │      │                     framework, requirement, changes         │   │    │
│  │      │                 )                                           │   │    │
│  │      │                                                             │   │    │
│  │      │  OUTPUT: List[RiskFinding] (12 compliance findings)        │   │    │
│  │      └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                         │    │
│  │  RESULT AGGREGATION                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  all_findings = []                                              │   │    │
│  │  │  for analyzer in risk_analyzers:                               │   │    │
│  │  │      try:                                                       │   │    │
│  │  │          analyzer_findings = await analyzer.analyze(diff)      │   │    │
│  │  │          all_findings.extend(analyzer_findings)                │   │    │
│  │  │          logger.info(f"{analyzer} completed: "                 │   │    │
│  │  │                      f"{len(analyzer_findings)} findings")     │   │    │
│  │  │      except Exception as e:                                    │   │    │
│  │  │          logger.error(f"{analyzer} failed: {e}")               │   │    │
│  │  │          continue  # Continue with other analyzers             │   │    │
│  │  │                                                                 │   │    │
│  │  │  TOTAL FINDINGS: 114 (45+23+34+12)                             │   │    │
│  │  │  ├─ CRITICAL: 3                                                 │   │    │
│  │  │  ├─ HIGH: 15                                                    │   │    │
│  │  │  ├─ MEDIUM: 86                                                  │   │    │
│  │  │  └─ LOW: 10                                                     │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 3: RISK PRIORITIZATION & ASSESSMENT                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  def _calculate_overall_risk_level(findings):                           │    │
│  │                                                                         │    │
│  │      risk_weights = {                                                   │    │
│  │          RiskLevel.CRITICAL: 100,                                       │    │
│  │          RiskLevel.HIGH: 75,                                            │    │
│  │          RiskLevel.MEDIUM: 50,                                          │    │
│  │          RiskLevel.LOW: 25                                              │    │
│  │      }                                                                  │    │
│  │                                                                         │    │
│  │      total_score = sum(risk_weights[f.risk_level] for f in findings)    │    │
│  │      finding_count = len(findings)                                      │    │
│  │      average_score = total_score / finding_count if finding_count > 0   │    │
│  │                                                                         │    │
│  │      if any(f.risk_level == CRITICAL for f in findings):               │    │
│  │          return RiskLevel.HIGH  # Any critical finding elevates risk    │    │
│  │      elif average_score >= 75:                                          │    │
│  │          return RiskLevel.HIGH                                          │    │
│  │      elif average_score >= 50:                                          │    │
│  │          return RiskLevel.MEDIUM                                        │    │
│  │      else:                                                              │    │
│  │          return RiskLevel.LOW                                           │    │
│  │                                                                         │    │
│  │  CALCULATED OVERALL RISK: MEDIUM                                        │    │
│  │  ├─ Reason: 3 CRITICAL findings detected                               │    │
│  │  ├─ Key Concerns: IAM permission changes, cross-account access         │    │
│  │  └─ Immediate Actions: Test in non-prod, validate IAM changes          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 4: RESULT PACKAGING                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  return RuleBasedAnalysisResult(                                        │    │
│  │      findings=all_findings,                                             │    │
│  │      overall_risk_level=calculated_risk,                                │    │
│  │      analysis_summary={                                                 │    │
│  │          "total_findings": 114,                                         │    │
│  │          "critical_findings": 3,                                        │    │
│  │          "high_findings": 15,                                           │    │
│  │          "analyzer_results": {                                          │    │
│  │              "security": 45,                                            │    │
│  │              "network": 23,                                             │    │
│  │              "operational": 34,                                         │    │
│  │              "compliance": 12                                           │    │
│  │          },                                                             │    │
│  │          "key_concerns": [                                              │    │
│  │              "IAM permission changes",                                  │    │
│  │              "Cross-account role modifications",                        │    │
│  │              "Network routing updates"                                  │    │
│  │          ]                                                              │    │
│  │      },                                                                 │    │
│  │      processing_metadata={                                              │    │
│  │          "analysis_duration": "12.3 seconds",                          │    │
│  │          "analyzers_executed": 4,                                       │    │
│  │          "errors_encountered": 0                                        │    │
│  │      }                                                                  │    │
│  │  )                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Risk Finding Decision Tree

```
┌─── RISK LEVEL DETERMINATION DECISION TREE ───────────────────────────────────────┐
│                                                                                  │
│                              Resource Change Detected                            │
│                                        │                                        │
│                                        ▼                                        │
│                              Is it an IAM Resource?                             │
│                                   ┌─────┴─────┐                                 │
│                                 YES│         │NO                               │
│                                   ▼           ▼                                 │
│                      ┌─ IAM Analysis ─┐  ┌─ Resource Type ─┐                    │
│                      │                │  │   Analysis     │                    │
│                      │ Is High-Risk   │  │                │                    │
│                      │ Action?        │  │ Network?       │                    │
│                      │ (iam:*, sts:*) │  │ ┌─────┴─────┐  │                    │
│                      │ ┌─────┴─────┐  │  │YES│       │NO│  │                    │
│                      │YES│       │NO│  │  │   ▼         ▼ │  │                    │
│                      │   ▼         ▼ │  │ Network   Other │  │                    │
│                      │CRITICAL   HIGH│  │Analysis  Resource│  │                    │
│                      │             │ │  │   │      Analysis│  │                    │
│                      │ Cross-Account?│ │  │   ▼         │  │  │                    │
│                      │ ┌─────┴─────┐ │ │  │ Routing     │  │  │                    │
│                      │YES│       │NO││ │  │ Impact?     │  │  │                    │
│                      │   ▼         ▼││ │  │ ┌─────┴───┐ │  │  │                    │
│                      │ HIGH     MEDIUM││ │  │HIGH│  │MED││  │  │                    │
│                      └───────────────┘│ │  │     ▼   ▼ ││  │  │                    │
│                                       │ │  │   Assess  ││  │  │                    │
│                      Is Resource      │ │  │   Impact  ││  │  │                    │
│                      Deletion?        │ │  └───────────┘│  │  │                    │
│                      ┌─────┴─────┐    │ │              │  │  │                    │
│                    YES│         │NO   │ │              │  │  │                    │
│                      ▼           ▼    │ │              │  │  │                    │
│                   Data Risk    LOW     │ │              │  │  │                    │
│                   Assessment          │ │              │  │  │                    │
│                   ┌─────┴─────┐       │ │              │  │  │                    │
│                 YES│         │NO      │ │              │  │  │                    │
│                   ▼           ▼       │ │              │  │  │                    │
│                CRITICAL     HIGH      │ │              │  │  │                    │
│                                       │ │              │  │  │                    │
│                              Final Risk Level          │  │  │                    │
│                              Determination             │  │  │                    │
│                              ┌─────────────────────┐   │  │  │                    │
│                              │                     │   │  │  │                    │
│                              │ Combine individual  │   │  │  │                    │
│                              │ risk assessments:   │   │  │  │                    │
│                              │                     │   │  │  │                    │
│                              │ • Security risks    │◄──┘  │  │                    │
│                              │ • Network risks     │◄─────┘  │                    │
│                              │ • Operational risks │◄────────┘                    │
│                              │ • Compliance risks  │                             │
│                              │                     │                             │
│                              │ Apply weighting:    │                             │
│                              │ CRITICAL = 100 pts  │                             │
│                              │ HIGH = 75 pts       │                             │
│                              │ MEDIUM = 50 pts     │                             │
│                              │ LOW = 25 pts        │                             │
│                              │                     │                             │
│                              │ Calculate average   │                             │
│                              │ and determine       │                             │
│                              │ overall risk level  │                             │
│                              └─────────────────────┘                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Report Generation Pipeline

### Multi-Format Report Generation Workflow

```
┌─── REPORT GENERATION PIPELINE ───────────────────────────────────────────────────┐
│                                                                                  │
│  INPUT: ComprehensiveAnalysisResult                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  • analysis_id: "uuid-12345"                                           │    │
│  │  • timestamp: 2025-06-25T10:30:00Z                                     │    │
│  │  • diff_analysis: DiffAnalysis (74 stacks, 225 resources, 462 IAM)     │    │
│  │  • rule_based_analysis: RuleBasedAnalysisResult (114 findings)         │    │
│  │  • llm_analysis: LLMAnalysisResult (4 specialized insights)            │    │
│  │  • combined_assessment: CombinedAssessment (MEDIUM risk level)         │    │
│  │  • analysis_metadata: AnalysisMetadata (duration, provider, etc.)      │    │
│  │                                                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 1: FORMAT SELECTION & ROUTING                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  CLI Options Processing:                                                │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  if args.format == "json":                                      │   │    │
│  │  │      output_manager.save_json(analysis_results)                 │   │    │
│  │  │  elif args.format == "yaml":                                    │   │    │
│  │  │      output_manager.save_yaml(analysis_results)                 │   │    │
│  │  │  elif args.format == "html":                                    │   │    │
│  │  │      output_manager.save_html(analysis_results)                 │   │    │
│  │  │  elif args.generate_reports:                                    │   │    │
│  │  │      enterprise_reports.generate_all_reports(analysis_results)  │   │    │
│  │  │  else:                                                           │   │    │
│  │  │      # Default: Admin-friendly console output                   │   │    │
│  │  │      admin_formatter.format_for_console(analysis_results)       │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  │                                                                         │    │
│  │  Parallel Report Generation Paths:                                     │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │    │
│  │  │   JSON/     │ │   Admin     │ │ Enterprise  │ │ Interactive │      │    │
│  │  │    YAML     │ │  Friendly   │ │   Reports   │ │   Session   │      │    │
│  │  │ Serializer  │ │  Formatter  │ │  Generator  │ │  Interface  │      │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │    │
│  │        │               │               │               │              │    │
│  │        ▼               ▼               ▼               ▼              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 2: ENTERPRISE REPORT GENERATION (DetailedPath)                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  EnterpriseReportGenerator.generate_all_reports(analysis_results)       │    │
│  │                                                                         │    │
│  │  ┌─ REPORT TYPE SELECTION ────────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  report_types = [                                                 │ │    │
│  │  │      "executive_summary",      # C-Level audience                │ │    │
│  │  │      "technical_report",       # Engineering teams               │ │    │
│  │  │      "risk_matrix",            # Security teams                  │ │    │
│  │  │      "compliance_report",      # Audit teams                     │ │    │
│  │  │      "full_report"             # Complete analysis               │ │    │
│  │  │  ]                                                                │ │    │
│  │  │                                                                   │ │    │
│  │  │  for report_type in report_types:                                 │ │    │
│  │  │      await generate_report_async(report_type, analysis_results)   │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ EXECUTIVE SUMMARY GENERATION ─────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def generate_executive_summary(analysis_results):                │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Data Preparation                                           │ │    │
│  │  │      exec_data = {                                                │ │    │
│  │  │          "analysis_overview": {                                   │ │    │
│  │  │              "total_stacks": 74,                                  │ │    │
│  │  │              "total_changes": 225,                                │ │    │
│  │  │              "iam_changes": 462,                                  │ │    │
│  │  │              "analysis_date": "2025-06-25",                       │ │    │
│  │  │              "lza_version_change": "1.10.0 → 1.12.1"             │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "risk_summary": {                                        │ │    │
│  │  │              "overall_risk": "MEDIUM",                            │ │    │
│  │  │              "critical_issues": 3,                                │ │    │
│  │  │              "high_priority": 15,                                 │ │    │
│  │  │              "key_concerns": [                                    │ │    │
│  │  │                  "IAM permission changes",                        │ │    │
│  │  │                  "Cross-account role modifications",              │ │    │
│  │  │                  "Network routing updates"                        │ │    │
│  │  │              ]                                                    │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "business_impact": {                                     │ │    │
│  │  │              "deployment_recommendation": "PROCEED_WITH_CAUTION", │ │    │
│  │  │              "testing_required": True,                            │ │    │
│  │  │              "rollback_complexity": "MEDIUM",                     │ │    │
│  │  │              "estimated_downtime": "< 30 minutes"                 │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "immediate_actions": [                                   │ │    │
│  │  │              "Test IAM changes in non-production environment",    │ │    │
│  │  │              "Validate cross-account access functionality",       │ │    │
│  │  │              "Review network routing table modifications",        │ │    │
│  │  │              "Prepare rollback procedures for critical changes"   │ │    │
│  │  │          ]                                                        │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Template Rendering                                         │ │    │
│  │  │      template = self.jinja_env.get_template('executive_summary')  │ │    │
│  │  │      html_content = template.render(**exec_data)                  │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Output Generation                                          │ │    │
│  │  │      output_path = "output/reports/executive_summary.html"        │ │    │
│  │  │      with open(output_path, 'w') as f:                            │ │    │
│  │  │          f.write(html_content)                                    │ │    │
│  │  │                                                                   │ │    │
│  │  │      return output_path                                           │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ TECHNICAL REPORT GENERATION ──────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def generate_technical_report(analysis_results):                 │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Detailed Data Preparation                                  │ │    │
│  │  │      tech_data = {                                                │ │    │
│  │  │          "analysis_metadata": analysis_results.analysis_metadata, │ │    │
│  │  │          "rule_based_findings": {                                 │ │    │
│  │  │              "security_findings": [                               │ │    │
│  │  │                  {                                                │ │    │
│  │  │                      "finding_id": "SEC-001",                     │ │    │
│  │  │                      "title": "High-Risk IAM Permission Change",  │ │    │
│  │  │                      "description": "Role policy modified...",    │ │    │
│  │  │                      "risk_level": "HIGH",                        │ │    │
│  │  │                      "affected_resource": "CrossAccountRole",     │ │    │
│  │  │                      "stack_name": "DependenciesStack",           │ │    │
│  │  │                      "recommendations": [                         │ │    │
│  │  │                          "Review trust relationships",            │ │    │
│  │  │                          "Test cross-account access"              │ │    │
│  │  │                      ],                                           │ │    │
│  │  │                      "rollback_steps": [                          │ │    │
│  │  │                          "Revert to previous role policy",        │ │    │
│  │  │                          "Update trust relationships"             │ │    │
│  │  │                      ]                                            │ │    │
│  │  │                  }                                                │ │    │
│  │  │                  # ... 44 more security findings                  │ │    │
│  │  │              ],                                                   │ │    │
│  │  │              "network_findings": [...],  # 23 findings            │ │    │
│  │  │              "operational_findings": [...],  # 34 findings        │ │    │
│  │  │              "compliance_findings": [...]   # 12 findings         │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "llm_insights": {                                        │ │    │
│  │  │              "overall_assessment": "Standard LZA upgrade...",     │ │    │
│  │  │              "network_impact": "Hub-spoke connectivity...",       │ │    │
│  │  │              "security_impact": "Cross-account roles...",         │ │    │
│  │  │              "operational_readiness": "Test IAM in non-prod..."   │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "detailed_changes": {                                    │ │    │
│  │  │              "stacks_modified": analysis_results.diff_analysis.stack_diffs, │ │
│  │  │              "resource_changes_by_type": group_by_resource_type(),│ │    │
│  │  │              "iam_changes_detailed": analyze_iam_changes(),       │ │    │
│  │  │              "property_level_changes": extract_property_changes() │ │    │
│  │  │          }                                                        │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Template Rendering with Enhanced Styling                   │ │    │
│  │  │      template = self.jinja_env.get_template('technical_report')   │ │    │
│  │  │      html_content = template.render(**tech_data)                  │ │    │
│  │  │                                                                   │ │    │
│  │  │      return "output/reports/technical_report.html"                │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ RISK MATRIX VISUALIZATION ─────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def generate_risk_matrix(analysis_results):                      │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Risk Matrix Data Preparation                               │ │    │
│  │  │      risk_matrix = {                                              │ │    │
│  │  │          "matrix_data": [                                         │ │    │
│  │  │              # [Impact, Likelihood, Count, Examples]              │ │    │
│  │  │              ["CRITICAL", "HIGH", 2, ["IAM Admin Access"]],       │ │    │
│  │  │              ["CRITICAL", "MEDIUM", 1, ["KMS Key Deletion"]],     │ │    │
│  │  │              ["HIGH", "HIGH", 8, ["Cross-Account Roles"]],        │ │    │
│  │  │              ["HIGH", "MEDIUM", 7, ["Network Routes"]],           │ │    │
│  │  │              ["MEDIUM", "HIGH", 15, ["Security Groups"]],         │ │    │
│  │  │              ["MEDIUM", "MEDIUM", 71, ["Parameter Updates"]],     │ │    │
│  │  │              ["LOW", "LOW", 10, ["Description Changes"]]          │ │    │
│  │  │          ],                                                       │ │    │
│  │  │          "risk_categories": {                                     │ │    │
│  │  │              "security": {"count": 45, "highest": "CRITICAL"},    │ │    │
│  │  │              "network": {"count": 23, "highest": "HIGH"},         │ │    │
│  │  │              "operational": {"count": 34, "highest": "HIGH"},     │ │    │
│  │  │              "compliance": {"count": 12, "highest": "MEDIUM"}     │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "visualization_data": generate_d3_compatible_data()      │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Interactive Visualization Generation                       │ │    │
│  │  │      template = self.jinja_env.get_template('risk_matrix')        │ │    │
│  │  │      html_content = template.render(**risk_matrix)                │ │    │
│  │  │                                                                   │ │    │
│  │  │      return "output/reports/risk_matrix.html"                     │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ COMPLIANCE MAPPING REPORT ─────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def generate_compliance_report(analysis_results):                │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Compliance Framework Mapping                               │ │    │
│  │  │      compliance_data = {                                          │ │    │
│  │  │          "framework_impacts": {                                   │ │    │
│  │  │              "SOC2_Type_II": {                                    │ │    │
│  │  │                  "affected_controls": [                           │ │    │
│  │  │                      "CC6.1 - Logical Access Controls",           │ │    │
│  │  │                      "CC6.2 - Authentication",                    │ │    │
│  │  │                      "CC6.3 - Authorization"                      │ │    │
│  │  │                  ],                                               │ │    │
│  │  │                  "risk_level": "MEDIUM",                          │ │    │
│  │  │                  "findings_count": 8,                             │ │    │
│  │  │                  "recommendations": [                             │ │    │
│  │  │                      "Document IAM role changes",                 │ │    │
│  │  │                      "Update access control documentation"        │ │    │
│  │  │                  ]                                                │ │    │
│  │  │              },                                                   │ │    │
│  │  │              "PCI_DSS": {                                         │ │    │
│  │  │                  "affected_requirements": ["3.4", "7.1", "8.1"],  │ │    │
│  │  │                  "risk_level": "LOW",                             │ │    │
│  │  │                  "findings_count": 2                              │ │    │
│  │  │              }                                                    │ │    │
│  │  │              # ... GDPR, HIPAA, ISO27001 mappings                │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "audit_trail": {                                         │ │    │
│  │  │              "analysis_timestamp": analysis_results.timestamp,    │ │    │
│  │  │              "analysis_method": "Automated + LLM Enhanced",       │ │    │
│  │  │              "reviewer": "LZA Diff Analyzer v1.0",                │ │    │
│  │  │              "confidence_level": "HIGH"                           │ │    │
│  │  │          }                                                        │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      template = self.jinja_env.get_template('compliance_report')  │ │    │
│  │  │      html_content = template.render(**compliance_data)            │ │    │
│  │  │                                                                   │ │    │
│  │  │      return "output/reports/compliance_report.html"               │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 3: ADMIN-FRIENDLY CONSOLE OUTPUT                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  AdminFriendlyFormatter.format_for_console(analysis_results)            │    │
│  │                                                                         │    │
│  │  ┌─ CONSOLE OUTPUT GENERATION ────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  # Rich Console Formatting                                        │ │    │
│  │  │  console = Console()                                              │ │    │
│  │  │                                                                   │ │    │
│  │  │  # Executive Summary Panel                                        │ │    │
│  │  │  console.print(Panel(                                             │ │    │
│  │  │      f"🔍 EXECUTIVE SUMMARY\n"                                    │ │    │
│  │  │      f"Your LZA upgrade from 1.10.0 to 1.12.1 affects "          │ │    │
│  │  │      f"{total_stacks} stacks across multiple accounts.\n"         │ │    │
│  │  │      f"Total changes detected: {total_changes} resources, "       │ │    │
│  │  │      f"{iam_changes} IAM modifications.",                          │ │    │
│  │  │      title="Analysis Overview",                                   │ │    │
│  │  │      style="blue"                                                 │ │    │
│  │  │  ))                                                               │ │    │
│  │  │                                                                   │ │    │
│  │  │  # Key Concerns with Risk-Based Color Coding                      │ │    │
│  │  │  console.print(Panel(                                             │ │    │
│  │  │      f"⚠️  KEY CONCERNS (Requires Your Review):\n"                │ │    │
│  │  │      f"1. IAM Permission Changes ({iam_findings_count} findings)\n"│ │    │
│  │  │      f"   └─ Why: Roles and policies are being modified...\n"     │ │    │
│  │  │      f"   └─ Action: Review cross-account access in ...",         │ │    │
│  │  │      title="Risk Assessment",                                     │ │    │
│  │  │      style="yellow"                                               │ │    │
│  │  │  ))                                                               │ │    │
│  │  │                                                                   │ │    │
│  │  │  # Immediate Actions Checklist                                    │ │    │
│  │  │  console.print(Panel(                                             │ │    │
│  │  │      f"🎯 IMMEDIATE ACTIONS:\n"                                   │ │    │
│  │  │      f"□ Test IAM changes in non-production environment first\n"  │ │    │
│  │  │      f"□ Review IAM changes for unintended privilege escalation\n"│ │    │
│  │  │      f"□ Validate automation scripts work with updated params\n"  │ │    │
│  │  │      f"□ Backup current configurations before proceeding",        │ │    │
│  │  │      title="Next Steps",                                          │ │    │
│  │  │      style="green"                                                │ │    │
│  │  │  ))                                                               │ │    │
│  │  │                                                                   │ │    │
│  │  │  # LLM Insights (if available)                                    │ │    │
│  │  │  if llm_insights:                                                 │ │    │
│  │  │      console.print(Panel(                                         │ │    │
│  │  │          f"🤖 AI-POWERED INSIGHTS\n"                              │ │    │
│  │  │          f"{llm_insights.overall_assessment}\n\n"                 │ │    │
│  │  │          f"Network Impact: {llm_insights.network_impact}\n"       │ │    │
│  │  │          f"Security Impact: {llm_insights.security_impact}",      │ │    │
│  │  │          title="Enhanced Analysis",                               │ │    │
│  │  │          style="cyan"                                             │ │    │
│  │  │      ))                                                           │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 4: OUTPUT FILE MANAGEMENT                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  FileManager.create_output_structure()                                 │    │
│  │                                                                         │    │
│  │  output/                                                                │    │
│  │  ├── analysis/                                                          │    │
│  │  │   ├── diff_analysis.json              (Machine-readable raw data)   │    │
│  │  │   ├── comprehensive_analysis.json     (Complete analysis results)   │    │
│  │  │   └── analysis_summary.yaml           (Human-readable summary)      │    │
│  │  │                                                                     │    │
│  │  ├── reports/                                                           │    │
│  │  │   ├── executive_summary.html          (C-Level dashboard)           │    │
│  │  │   ├── technical_report.html           (Engineering deep-dive)       │    │
│  │  │   ├── risk_matrix.html                (Security assessment)         │    │
│  │  │   ├── compliance_report.html          (Audit documentation)         │    │
│  │  │   └── full_report.html                (Complete combined report)    │    │
│  │  │                                                                     │    │
│  │  ├── logs/                                                             │    │
│  │  │   ├── analysis.log                    (Processing logs)             │    │
│  │  │   └── llm_interactions.log            (LLM request/response)        │    │
│  │  │                                                                     │    │
│  │  └── temp/                                                             │    │
│  │      └── intermediate_results/           (Debug data)                  │    │
│  │                                                                         │    │
│  │  SUCCESS: All reports generated successfully                           │    │
│  │  ├─ Console output: Real-time progress and summary                     │    │
│  │  ├─ JSON/YAML files: Machine processing and archival                  │    │
│  │  ├─ HTML reports: Stakeholder-specific documentation                   │    │
│  │  └─ Interactive option: Q&A session availability                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Report Template Architecture

```
┌─── JINJA2 TEMPLATE SYSTEM ───────────────────────────────────────────────────────┐
│                                                                                  │
│  BASE TEMPLATE (base.html)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  <!DOCTYPE html>                                                        │    │
│  │  <html lang="en">                                                       │    │
│  │  <head>                                                                 │    │
│  │      <meta charset="UTF-8">                                             │    │
│  │      <meta name="viewport" content="width=device-width, initial-scale=1">│    │
│  │      <title>{% block title %}LZA Diff Analysis Report{% endblock %}</title> │
│  │      <style>                                                            │    │
│  │          /* Professional CSS Styling */                                 │    │
│  │          .risk-critical { color: #dc3545; font-weight: bold; }          │    │
│  │          .risk-high { color: #fd7e14; font-weight: bold; }              │    │
│  │          .risk-medium { color: #ffc107; }                               │    │
│  │          .risk-low { color: #28a745; }                                  │    │
│  │          .findings-table { border-collapse: collapse; width: 100%; }    │    │
│  │          /* ... more styling */                                         │    │
│  │      </style>                                                           │    │
│  │      {% block head %}{% endblock %}                                     │    │
│  │  </head>                                                                │    │
│  │  <body>                                                                 │    │
│  │      <header>                                                           │    │
│  │          <h1>{% block header %}LZA Diff Analysis{% endblock %}</h1>     │    │
│  │          <div class="analysis-metadata">                                │    │
│  │              Generated: {{ analysis_metadata.timestamp }}               │    │
│  │              Duration: {{ analysis_metadata.duration }}                 │    │
│  │          </div>                                                         │    │
│  │      </header>                                                          │    │
│  │      <main>                                                             │    │
│  │          {% block content %}{% endblock %}                              │    │
│  │      </main>                                                            │    │
│  │      <footer>                                                           │    │
│  │          <p>Generated by LZA Diff Analyzer v{{ version }}</p>           │    │
│  │      </footer>                                                          │    │
│  │  </body>                                                                │    │
│  │  </html>                                                                │    │
│  │                                                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  EXECUTIVE SUMMARY TEMPLATE (executive_summary.html)                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  {% extends "base.html" %}                                              │    │
│  │                                                                         │    │
│  │  {% block title %}Executive Summary - LZA Analysis{% endblock %}        │    │
│  │                                                                         │    │
│  │  {% block content %}                                                    │    │
│  │  <div class="executive-dashboard">                                      │    │
│  │      <div class="summary-cards">                                        │    │
│  │          <div class="card overview-card">                               │    │
│  │              <h3>Analysis Overview</h3>                                 │    │
│  │              <div class="metric">                                       │    │
│  │                  <span class="number">{{ analysis_overview.total_stacks }}</span> │
│  │                  <span class="label">Stacks Analyzed</span>             │    │
│  │              </div>                                                     │    │
│  │              <div class="metric">                                       │    │
│  │                  <span class="number">{{ analysis_overview.total_changes }}</span> │
│  │                  <span class="label">Resource Changes</span>            │    │
│  │              </div>                                                     │    │
│  │              <div class="version-change">                               │    │
│  │                  LZA Version: {{ analysis_overview.lza_version_change }} │    │
│  │              </div>                                                     │    │
│  │          </div>                                                         │    │
│  │                                                                         │    │
│  │          <div class="card risk-card">                                   │    │
│  │              <h3>Risk Assessment</h3>                                   │    │
│  │              <div class="risk-level risk-{{ risk_summary.overall_risk.lower() }}"> │
│  │                  {{ risk_summary.overall_risk }} RISK                   │    │
│  │              </div>                                                     │    │
│  │              <div class="risk-breakdown">                               │    │
│  │                  <div class="risk-metric">                              │    │
│  │                      <span class="risk-critical">{{ risk_summary.critical_issues }}</span> │
│  │                      Critical Issues                                    │    │
│  │                  </div>                                                 │    │
│  │                  <div class="risk-metric">                              │    │
│  │                      <span class="risk-high">{{ risk_summary.high_priority }}</span> │
│  │                      High Priority                                      │    │
│  │                  </div>                                                 │    │
│  │              </div>                                                     │    │
│  │          </div>                                                         │    │
│  │      </div>                                                             │    │
│  │                                                                         │    │
│  │      <div class="key-concerns">                                         │    │
│  │          <h3>Key Concerns Requiring Review</h3>                         │    │
│  │          <ul class="concerns-list">                                     │    │
│  │              {% for concern in risk_summary.key_concerns %}             │    │
│  │              <li class="concern-item">{{ concern }}</li>                │    │
│  │              {% endfor %}                                               │    │
│  │          </ul>                                                          │    │
│  │      </div>                                                             │    │
│  │                                                                         │    │
│  │      <div class="business-impact">                                      │    │
│  │          <h3>Business Impact Assessment</h3>                            │    │
│  │          <div class="impact-grid">                                      │    │
│  │              <div class="impact-item">                                  │    │
│  │                  <strong>Deployment Recommendation:</strong>            │    │
│  │                  <span class="recommendation-{{ business_impact.deployment_recommendation.lower() }}"> │
│  │                      {{ business_impact.deployment_recommendation }}    │    │
│  │                  </span>                                                │    │
│  │              </div>                                                     │    │
│  │              <div class="impact-item">                                  │    │
│  │                  <strong>Estimated Downtime:</strong>                   │    │
│  │                  {{ business_impact.estimated_downtime }}               │    │
│  │              </div>                                                     │    │
│  │          </div>                                                         │    │
│  │      </div>                                                             │    │
│  │                                                                         │    │
│  │      <div class="immediate-actions">                                    │    │
│  │          <h3>Immediate Actions Required</h3>                            │    │
│  │          <ol class="actions-checklist">                                 │    │
│  │              {% for action in immediate_actions %}                      │    │
│  │              <li class="action-item">                                   │    │
│  │                  <label>                                                │    │
│  │                      <input type="checkbox"> {{ action }}              │    │
│  │                  </label>                                               │    │
│  │              </li>                                                      │    │
│  │              {% endfor %}                                               │    │
│  │          </ol>                                                          │    │
│  │      </div>                                                             │    │
│  │  </div>                                                                 │    │
│  │  {% endblock %}                                                         │    │
│  │                                                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Configuration Management Flow

### YAML Configuration Cascade and Processing

```
┌─── CONFIGURATION MANAGEMENT SYSTEM ──────────────────────────────────────────────┐
│                                                                                  │
│  PHASE 1: CONFIGURATION FILE DISCOVERY & LOADING                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Application Startup                                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  def load_configuration():                                      │   │    │
│  │  │                                                                 │   │    │
│  │  │      # 1. Default Configuration Discovery                       │   │    │
│  │  │      config_paths = [                                           │   │    │
│  │  │          Path(__file__).parent.parent / "config" / "llm_config.yaml", │   │    │
│  │  │          Path.home() / ".lza-analyzer" / "config.yaml",         │   │    │
│  │  │          Path("/etc/lza-analyzer/config.yaml"),                 │   │    │
│  │  │          Path.cwd() / "config" / "llm_config.yaml"              │   │    │
│  │  │      ]                                                          │   │    │
│  │  │                                                                 │   │    │
│  │  │      # 2. Environment Variable Override                         │   │    │
│  │  │      if env_config_path := os.getenv("LZA_CONFIG_PATH"):        │   │    │
│  │  │          config_paths.insert(0, Path(env_config_path))          │   │    │
│  │  │                                                                 │   │    │
│  │  │      # 3. CLI Argument Override                                 │   │    │
│  │  │      if args.config:                                            │   │    │
│  │  │          config_paths.insert(0, Path(args.config))              │   │    │
│  │  │                                                                 │   │    │
│  │  │      # 4. Find First Valid Config                               │   │    │
│  │  │      for config_path in config_paths:                           │   │    │
│  │  │          if config_path.exists() and config_path.is_file():     │   │    │
│  │  │              return load_yaml_config(config_path)               │   │    │
│  │  │                                                                 │   │    │
│  │  │      # 5. Fallback to Default Configuration                     │   │    │
│  │  │      return create_default_config()                             │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ YAML FILE LOADING ─────────────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def load_yaml_config(config_path: Path):                        │ │    │
│  │  │                                                                   │ │    │
│  │  │      try:                                                         │ │    │
│  │  │          with open(config_path, 'r', encoding='utf-8') as f:      │ │    │
│  │  │              raw_config = yaml.safe_load(f)                      │ │    │
│  │  │                                                                   │ │    │
│  │  │          # Environment Variable Substitution                     │ │    │
│  │  │          processed_config = substitute_env_vars(raw_config)      │ │    │
│  │  │                                                                   │ │    │
│  │  │          # Validate Configuration Structure                       │ │    │
│  │  │          return validate_config_structure(processed_config)      │ │    │
│  │  │                                                                   │ │    │
│  │  │      except yaml.YAMLError as e:                                 │ │    │
│  │  │          logger.error(f"YAML parsing error in {config_path}: {e}")│ │    │
│  │  │          raise ConfigurationError(f"Invalid YAML: {e}")          │ │    │
│  │  │                                                                   │ │    │
│  │  │      except FileNotFoundError:                                   │ │    │
│  │  │          logger.warning(f"Config file not found: {config_path}") │ │    │
│  │  │          return None                                              │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 2: ENVIRONMENT VARIABLE SUBSTITUTION                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  def substitute_env_vars(config_dict):                                  │    │
│  │                                                                         │    │
│  │      ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')                     │    │
│  │                                                                         │    │
│  │      def substitute_recursive(obj):                                     │    │
│  │          if isinstance(obj, dict):                                      │    │
│  │              return {k: substitute_recursive(v) for k, v in obj.items()} │    │
│  │          elif isinstance(obj, list):                                    │    │
│  │              return [substitute_recursive(item) for item in obj]        │    │
│  │          elif isinstance(obj, str):                                     │    │
│  │              def replace_env_var(match):                                │    │
│  │                  env_var = match.group(1)                               │    │
│  │                  default_value = None                                   │    │
│  │                                                                         │    │
│  │                  # Handle default values: ${VAR:-default}               │    │
│  │                  if ':-' in env_var:                                    │    │
│  │                      env_var, default_value = env_var.split(':-', 1)   │    │
│  │                                                                         │    │
│  │                  value = os.getenv(env_var, default_value)              │    │
│  │                  if value is None:                                      │    │
│  │                      logger.warning(f"Environment variable {env_var} "  │    │
│  │                                     f"not set and no default provided") │    │
│  │                      return match.group(0)  # Return original           │    │
│  │                                                                         │    │
│  │                  return value                                           │    │
│  │                                                                         │    │
│  │              return ENV_VAR_PATTERN.sub(replace_env_var, obj)           │    │
│  │          else:                                                          │    │
│  │              return obj                                                 │    │
│  │                                                                         │    │
│  │      return substitute_recursive(config_dict)                          │    │
│  │                                                                         │    │
│  │  EXAMPLES:                                                              │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  Input YAML:                                                    │   │    │
│  │  │  providers:                                                     │   │    │
│  │  │    openai:                                                      │   │    │
│  │  │      api_key: ${OPENAI_API_KEY}                                 │   │    │
│  │  │      model: ${OPENAI_MODEL:-gpt-4o-mini}                        │   │    │
│  │  │      timeout: ${LLM_TIMEOUT:-30}                                │   │    │
│  │  │                                                                 │   │    │
│  │  │  Environment Variables:                                         │   │    │
│  │  │  OPENAI_API_KEY=sk-abc123...                                    │   │    │
│  │  │  # OPENAI_MODEL not set (will use default)                     │   │    │
│  │  │  LLM_TIMEOUT=45                                                 │   │    │
│  │  │                                                                 │   │    │
│  │  │  Processed Result:                                              │   │    │
│  │  │  providers:                                                     │   │    │
│  │  │    openai:                                                      │   │    │
│  │  │      api_key: "sk-abc123..."                                    │   │    │
│  │  │      model: "gpt-4o-mini"                                       │   │    │
│  │  │      timeout: "45"                                              │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 3: CONFIGURATION VALIDATION & TYPE CONVERSION                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Pydantic Model Validation                                              │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  class LLMConfigManager(BaseModel):                             │   │    │
│  │  │      default_provider: LLMProvider = LLMProvider.OLLAMA         │   │    │
│  │  │      max_retries: int = Field(default=3, ge=1, le=10)           │   │    │
│  │  │      retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)   │   │    │
│  │  │      fallback_chain: List[LLMProvider] = Field(default_factory=list) │   │    │
│  │  │      providers: Dict[LLMProvider, LLMConfig] = Field(default_factory=dict) │   │    │
│  │  │                                                                 │   │    │
│  │  │      @validator('fallback_chain')                               │   │    │
│  │  │      def validate_fallback_chain(cls, v, values):               │   │    │
│  │  │          if not v:  # Empty fallback chain                      │   │    │
│  │  │              return [values.get('default_provider', LLMProvider.OLLAMA)] │   │    │
│  │  │          return v                                               │   │    │
│  │  │                                                                 │   │    │
│  │  │      @validator('providers')                                    │   │    │
│  │  │      def validate_providers(cls, v, values):                    │   │    │
│  │  │          # Ensure default provider is configured                │   │    │
│  │  │          default_provider = values.get('default_provider')      │   │    │
│  │  │          if default_provider and default_provider not in v:     │   │    │
│  │  │              raise ValueError(f"Default provider {default_provider} " │   │    │
│  │  │                              f"not found in providers config") │   │    │
│  │  │          return v                                               │   │    │
│  │  │                                                                 │   │    │
│  │  │  class LLMConfig(BaseModel):                                    │   │    │
│  │  │      provider: LLMProvider                                      │   │    │
│  │  │      model: str                                                 │   │    │
│  │  │      temperature: float = Field(default=0.1, ge=0.0, le=2.0)   │   │    │
│  │  │      max_tokens: int = Field(default=4096, ge=1, le=32000)      │   │    │
│  │  │      timeout: int = Field(default=30, ge=1, le=300)             │   │    │
│  │  │      base_url: Optional[str] = None                             │   │    │
│  │  │      api_key: Optional[str] = None                              │   │    │
│  │  │      enabled: bool = True                                       │   │    │
│  │  │      additional_params: Dict[str, Any] = Field(default_factory=dict) │   │    │
│  │  │                                                                 │   │    │
│  │  │      @validator('api_key')                                      │   │    │
│  │  │      def validate_api_key(cls, v, values):                      │   │    │
│  │  │          provider = values.get('provider')                      │   │    │
│  │  │          if provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]: │   │    │
│  │  │              if not v:                                          │   │    │
│  │  │                  logger.warning(f"No API key provided for {provider}") │   │    │
│  │  │          return v                                               │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ VALIDATION RESULTS ────────────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  SUCCESS: LLMConfigManager instance created                       │ │    │
│  │  │  ├─ All required fields validated                                 │ │    │
│  │  │  ├─ Type conversions applied (strings to ints/floats/bools)       │ │    │
│  │  │  ├─ Range constraints enforced                                    │ │    │
│  │  │  ├─ Cross-field validations passed                                │ │    │
│  │  │  └─ Default values populated where needed                         │ │    │
│  │  │                                                                   │ │    │
│  │  │  FAILURE: ValidationError raised                                  │ │    │
│  │  │  ├─ Detailed error messages with field paths                      │ │    │
│  │  │  ├─ Type conversion failures                                      │ │    │
│  │  │  ├─ Range constraint violations                                   │ │    │
│  │  │  └─ Missing required fields                                       │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 4: CONFIGURATION DISTRIBUTION & USAGE                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Configuration Injection Pattern                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  # Singleton Configuration Manager                              │   │    │
│  │  │  config_manager = ConfigLoader.load_default_config()            │   │    │
│  │  │                                                                 │   │    │
│  │  │  # Component Initialization with Configuration                  │   │    │
│  │  │  analysis_engine = ComprehensiveAnalysisEngine(                 │   │    │
│  │  │      llm_config=config_manager                                  │   │    │
│  │  │  )                                                              │   │    │
│  │  │                                                                 │   │    │
│  │  │  llm_provider_factory = LLMProviderFactory(                     │   │    │
│  │  │      config_manager=config_manager                              │   │    │
│  │  │  )                                                              │   │    │
│  │  │                                                                 │   │    │
│  │  │  interactive_session = InteractiveSession(                      │   │    │
│  │  │      llm_config=config_manager                                  │   │    │
│  │  │  )                                                              │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ RUNTIME CONFIGURATION ACCESS ─────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  # LLM Provider Configuration Retrieval                          │ │    │
│  │  │  def get_provider_config(self, provider: LLMProvider):            │ │    │
│  │  │      """Get configuration for specific provider"""               │ │    │
│  │  │      return self.config_manager.get_llm_config(provider)         │ │    │
│  │  │                                                                   │ │    │
│  │  │  # Fallback Chain Access                                         │ │    │
│  │  │  def get_fallback_configs(self):                                 │ │    │
│  │  │      """Get ordered list of fallback configurations"""           │ │    │
│  │  │      configs = []                                                │ │    │
│  │  │      for provider_name in self.config_manager.fallback_chain:    │ │    │
│  │  │          provider_enum = LLMProvider(provider_name)              │ │    │
│  │  │          config = self.config_manager.get_llm_config(provider_enum) │ │    │
│  │  │          if config and config.enabled:                           │ │    │
│  │  │              configs.append(config)                              │ │    │
│  │  │      return configs                                              │ │    │
│  │  │                                                                   │ │    │
│  │  │  # Dynamic Configuration Updates                                 │ │    │
│  │  │  def update_provider_config(self, provider: LLMProvider,         │ │    │
│  │  │                            updates: Dict[str, Any]):             │ │    │
│  │  │      """Runtime configuration updates"""                        │ │    │
│  │  │      current_config = self.get_provider_config(provider)         │ │    │
│  │  │      updated_data = {**current_config.dict(), **updates}        │ │    │
│  │  │      new_config = LLMConfig(**updated_data)                      │ │    │
│  │  │      self.config_manager.providers[provider] = new_config       │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 5: CONFIGURATION MONITORING & RELOADING                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  def enable_config_hot_reload(self, config_path: Path):                │    │
│  │                                                                         │    │
│  │      from watchdog.observers import Observer                           │    │
│  │      from watchdog.events import FileSystemEventHandler               │    │
│  │                                                                         │    │
│  │      class ConfigFileHandler(FileSystemEventHandler):                  │    │
│  │          def __init__(self, config_manager):                           │    │
│  │              self.config_manager = config_manager                      │    │
│  │              self.last_reload = time.time()                            │    │
│  │                                                                         │    │
│  │          def on_modified(self, event):                                 │    │
│  │              if event.src_path.endswith('llm_config.yaml'):            │    │
│  │                  # Debounce: only reload every 2 seconds               │    │
│  │                  if time.time() - self.last_reload > 2:                │    │
│  │                      try:                                              │    │
│  │                          logger.info("Reloading configuration...")     │    │
│  │                          new_config = load_yaml_config(event.src_path) │    │
│  │                          self.config_manager.update(new_config)        │    │
│  │                          logger.info("Configuration reloaded successfully") │    │
│  │                          self.last_reload = time.time()                │    │
│  │                      except Exception as e:                           │    │
│  │                          logger.error(f"Config reload failed: {e}")    │    │
│  │                                                                         │    │
│  │      observer = Observer()                                             │    │
│  │      observer.schedule(                                                │    │
│  │          ConfigFileHandler(self),                                      │    │
│  │          str(config_path.parent),                                      │    │
│  │          recursive=False                                               │    │
│  │      )                                                                 │    │
│  │      observer.start()                                                  │    │
│  │                                                                         │    │
│  │  CONFIGURATION VALIDATION WORKFLOW:                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  1. File Change Detection                                       │   │    │
│  │  │     └─ Watchdog monitors config directory                       │   │    │
│  │  │                                                                 │   │    │
│  │  │  2. Change Validation                                           │   │    │
│  │  │     ├─ YAML syntax validation                                   │   │    │
│  │  │     ├─ Schema validation against Pydantic models               │   │    │
│  │  │     ├─ Environment variable substitution test                   │   │    │
│  │  │     └─ Cross-reference validation (providers exist)             │   │    │
│  │  │                                                                 │   │    │
│  │  │  3. Hot Reload Decision                                         │   │    │
│  │  │     ├─ If validation PASSES:                                    │   │    │
│  │  │     │   ├─ Update runtime configuration                         │   │    │
│  │  │     │   ├─ Notify all components of config change               │   │    │
│  │  │     │   └─ Log successful reload                                │   │    │
│  │  │     │                                                           │   │    │
│  │  │     └─ If validation FAILS:                                     │   │    │
│  │  │         ├─ Keep existing configuration                          │   │    │
│  │  │         ├─ Log validation errors                                │   │    │
│  │  │         └─ Send alert notification                              │   │    │
│  │  │                                                                 │   │    │
│  │  │  4. Component Notification                                      │   │    │
│  │  │     ├─ LLM Provider Factory: Refresh provider instances         │   │    │
│  │  │     ├─ Analysis Engine: Update LLM configuration                │   │    │
│  │  │     ├─ Interactive Session: Reconnect if needed                 │   │    │
│  │  │     └─ CLI Interface: Update help text and options              │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  CONFIGURATION HIERARCHY & OVERRIDE CHAIN                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Configuration Override Precedence (Highest to Lowest):                │    │
│  │                                                                         │    │
│  │  1. CLI Arguments                                                       │    │
│  │     ├─ --config /path/to/config.yaml                                   │    │
│  │     ├─ --llm-provider anthropic                                        │    │
│  │     ├─ --disable-llm                                                    │    │
│  │     └─ --enable-llm                                                     │    │
│  │                                                                         │    │
│  │  2. Environment Variables                                               │    │
│  │     ├─ LZA_CONFIG_PATH=/custom/path/config.yaml                         │    │
│  │     ├─ OPENAI_API_KEY=sk-...                                            │    │
│  │     ├─ ANTHROPIC_API_KEY=sk-ant-...                                     │    │
│  │     ├─ LLM_TIMEOUT=60                                                   │    │
│  │     └─ LZA_DEFAULT_PROVIDER=ollama                                      │    │
│  │                                                                         │    │
│  │  3. User Configuration File                                             │    │
│  │     └─ ~/.lza-analyzer/config.yaml                                      │    │
│  │                                                                         │    │
│  │  4. Project Configuration File                                          │    │
│  │     └─ ./config/llm_config.yaml                                         │    │
│  │                                                                         │    │
│  │  5. System Configuration File                                           │    │
│  │     └─ /etc/lza-analyzer/config.yaml                                    │    │
│  │                                                                         │    │
│  │  6. Built-in Defaults                                                   │    │
│  │     ├─ provider: ollama                                                 │    │
│  │     ├─ model: phi4:latest                                               │    │
│  │     ├─ temperature: 0.1                                                 │    │
│  │     ├─ timeout: 30                                                      │    │
│  │     └─ max_retries: 3                                                   │    │
│  │                                                                         │    │
│  │  EXAMPLE CONFIGURATION MERGE:                                           │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │    │
│  │  │                                                                 │   │    │
│  │  │  Base Config (llm_config.yaml):                                │   │    │
│  │  │  default_provider: ollama                                       │   │    │
│  │  │  providers:                                                     │   │    │
│  │  │    ollama:                                                      │   │    │
│  │  │      model: phi4:latest                                         │   │    │
│  │  │      timeout: 30                                                │   │    │
│  │  │                                                                 │   │    │
│  │  │  Environment Override:                                          │   │    │
│  │  │  LLM_TIMEOUT=45                                                 │   │    │
│  │  │  OPENAI_API_KEY=sk-abc123                                       │   │    │
│  │  │                                                                 │   │    │
│  │  │  CLI Override:                                                  │   │    │
│  │  │  --llm-provider openai                                          │   │    │
│  │  │                                                                 │   │    │
│  │  │  Final Merged Configuration:                                    │   │    │
│  │  │  default_provider: openai  # CLI override                       │   │    │
│  │  │  providers:                                                     │   │    │
│  │  │    ollama:                                                      │   │    │
│  │  │      model: phi4:latest                                         │   │    │
│  │  │      timeout: 45  # Environment override                        │   │    │
│  │  │    openai:                                                      │   │    │
│  │  │      api_key: sk-abc123  # Environment                          │   │    │
│  │  │      model: gpt-4o-mini  # Default                              │   │    │
│  │  │      timeout: 45  # Environment override                        │   │    │
│  │  │                                                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

*[Configuration Management Flow section completed. Next: Error Handling and Recovery]*

## Error Handling and Recovery

### Graceful Degradation and Recovery Patterns

```
┌─── ERROR HANDLING & RECOVERY SYSTEM ─────────────────────────────────────────────┐
│                                                                                  │
│  PHASE 1: ERROR DETECTION & CLASSIFICATION                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Error Hierarchy and Classification System                             │    │
│  │                                                                         │    │
│  │  ┌─ CRITICAL ERRORS (System Halt) ───────────────────────────────────┐  │    │
│  │  │                                                                   │  │    │
│  │  │  • ConfigurationError                                             │  │    │
│  │  │    ├─ Invalid YAML syntax                                         │  │    │
│  │  │    ├─ Missing required configuration files                        │  │    │
│  │  │    ├─ Pydantic validation failures                                │  │    │
│  │  │    └─ Circular dependency in fallback chain                       │  │    │
│  │  │                                                                   │  │    │
│  │  │  • FileSystemError                                                │  │    │
│  │  │    ├─ Input directory not found                                   │  │    │
│  │  │    ├─ No .diff files found                                        │  │    │
│  │  │    ├─ Permission denied for output directory                      │  │    │
│  │  │    └─ Disk space exhausted                                        │  │    │
│  │  │                                                                   │  │    │
│  │  │  • SecurityError                                                  │  │    │
│  │  │    ├─ Path traversal attempt detected                             │  │    │
│  │  │    ├─ Malicious input patterns                                    │  │    │
│  │  │    └─ API key validation failure                                  │  │    │
│  │  │                                                                   │  │    │
│  │  └───────────────────────────────────────────────────────────────────┘  │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ RECOVERABLE ERRORS (Graceful Degradation) ───────────────────────┐  │    │
│  │  │                                                                   │  │    │
│  │  │  • LLMError                                                       │  │    │
│  │  │    ├─ Provider unavailable (service down)                         │  │    │
│  │  │    ├─ API rate limit exceeded                                     │  │    │
│  │  │    ├─ Authentication failure (invalid API key)                    │  │    │
│  │  │    ├─ Network timeout                                             │  │    │
│  │  │    ├─ Model not found                                             │  │    │
│  │  │    └─ Response parsing error                                      │  │    │
│  │  │                                                                   │  │    │
│  │  │  • ParsingError                                                   │  │    │
│  │  │    ├─ Malformed diff file                                         │  │    │
│  │  │    ├─ Unexpected diff format                                      │  │    │
│  │  │    ├─ Missing required sections                                   │  │    │
│  │  │    └─ Character encoding issues                                   │  │    │
│  │  │                                                                   │  │    │
│  │  │  • AnalysisError                                                  │  │    │
│  │  │    ├─ Risk analyzer failure                                       │  │    │
│  │  │    ├─ Resource categorization failure                             │  │    │
│  │  │    ├─ Template rendering error                                    │  │    │
│  │  │    └─ Report generation failure                                   │  │    │
│  │  │                                                                   │  │    │
│  │  └───────────────────────────────────────────────────────────────────┘  │    │
│  │                                      │                                  │    │
│  │                                      ▼                                  │    │
│  │  ┌─ WARNING CONDITIONS (Continue with Notification) ─────────────────┐  │    │
│  │  │                                                                   │  │    │
│  │  │  • PerformanceWarning                                             │  │    │
│  │  │    ├─ Large file processing (>100MB)                              │  │    │
│  │  │    ├─ High stack count (>500 stacks)                              │  │    │
│  │  │    ├─ LLM response latency high (>30s)                            │  │    │
│  │  │    └─ Memory usage approaching limits                             │  │    │
│  │  │                                                                   │  │    │
│  │  │  • QualityWarning                                                 │  │    │
│  │  │    ├─ LLM confidence score low (<0.7)                             │  │    │
│  │  │    ├─ Incomplete parsing (some sections skipped)                  │  │    │
│  │  │    ├─ Unusual diff patterns detected                              │  │    │
│  │  │    └─ Missing metadata (account, region info)                     │  │    │
│  │  │                                                                   │  │    │
│  │  └───────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 2: RECOVERY STRATEGY SELECTION                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Recovery Decision Matrix                                               │    │
│  │                                                                         │    │
│  │  ┌─ LLM PROVIDER FAILURES ─────────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  async def _perform_llm_analysis(self, diff_analysis, provider):   │ │    │
│  │  │                                                                   │ │    │
│  │  │      providers_to_try = self._build_provider_chain(provider)      │ │    │
│  │  │                                                                   │ │    │
│  │  │      for attempt, config in enumerate(providers_to_try):          │ │    │
│  │  │          try:                                                     │ │    │
│  │  │              provider_instance = LLMProviderFactory.create_provider(config) │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Pre-flight Check                                   │ │    │
│  │  │              if not provider_instance.is_available():             │ │    │
│  │  │                  logger.warning(f"{config.provider} unavailable") │ │    │
│  │  │                  continue                                         │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Attempt Analysis                                   │ │    │
│  │  │              response = await provider_instance.generate(messages) │ │    │
│  │  │              logger.info(f"Analysis successful with {config.provider}") │ │    │
│  │  │              return self._parse_llm_response(response)            │ │    │
│  │  │                                                                   │ │    │
│  │  │          except LLMError as e:                                    │ │    │
│  │  │              logger.warning(f"LLM failure on {config.provider}: {e}") │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Rate Limit Handling                                │ │    │
│  │  │              if "rate limit" in str(e).lower():                   │ │    │
│  │  │                  retry_delay = min(30 * (2 ** attempt), 300)      │ │    │
│  │  │                  logger.info(f"Rate limited, waiting {retry_delay}s") │ │    │
│  │  │                  await asyncio.sleep(retry_delay)                 │ │    │
│  │  │                  continue  # Retry same provider                  │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Network/Timeout Handling                          │ │    │
│  │  │              if "timeout" in str(e).lower() or "network" in str(e).lower(): │ │    │
│  │  │                  if attempt < self.config.max_retries:            │ │    │
│  │  │                      await asyncio.sleep(self.config.retry_delay) │ │    │
│  │  │                      continue  # Retry same provider              │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Provider-specific Errors: Move to Next Provider    │ │    │
│  │  │              continue                                             │ │    │
│  │  │                                                                   │ │    │
│  │  │          except Exception as e:                                   │ │    │
│  │  │              logger.error(f"Unexpected error with {config.provider}: {e}") │ │    │
│  │  │              continue                                             │ │    │
│  │  │                                                                   │ │    │
│  │  │      # All providers failed - Graceful degradation               │ │    │
│  │  │      logger.warning("All LLM providers failed, continuing with rule-based only") │ │    │
│  │  │      return self._create_fallback_llm_result()                    │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ PARSING FAILURES ──────────────────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def parse_directory(self, directory: Path) -> DiffAnalysis:      │ │    │
│  │  │                                                                   │ │    │
│  │  │      analysis = DiffAnalysis()                                    │ │    │
│  │  │      errors = []                                                  │ │    │
│  │  │      successful_parses = 0                                        │ │    │
│  │  │                                                                   │ │    │
│  │  │      for file_path in diff_files:                                 │ │    │
│  │  │          try:                                                     │ │    │
│  │  │              stack_diff = self.parse_file(file_path)              │ │    │
│  │  │              analysis.stack_diffs.append(stack_diff)              │ │    │
│  │  │              successful_parses += 1                               │ │    │
│  │  │                                                                   │ │    │
│  │  │          except ParsingError as e:                                │ │    │
│  │  │              errors.append(f"{file_path.name}: {e}")              │ │    │
│  │  │              logger.warning(f"Parsing failed for {file_path}: {e}") │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Attempt Partial Recovery                           │ │    │
│  │  │              try:                                                 │ │    │
│  │  │                  partial_diff = self._attempt_partial_parse(file_path) │ │    │
│  │  │                  if partial_diff:                                 │ │    │
│  │  │                      analysis.stack_diffs.append(partial_diff)    │ │    │
│  │  │                      logger.info(f"Partial recovery for {file_path}") │ │    │
│  │  │              except Exception:                                    │ │    │
│  │  │                  logger.debug(f"Partial recovery failed for {file_path}") │ │    │
│  │  │                                                                   │ │    │
│  │  │          except Exception as e:                                   │ │    │
│  │  │              errors.append(f"{file_path.name}: Unexpected error") │ │    │
│  │  │              logger.error(f"Unexpected parsing error: {e}")       │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Assessment of Parsing Success                              │ │    │
│  │  │      total_files = len(diff_files)                                │ │    │
│  │  │      success_rate = successful_parses / total_files if total_files > 0 else 0 │ │    │
│  │  │                                                                   │ │    │
│  │  │      if success_rate < 0.5:  # Less than 50% success              │ │    │
│  │  │          raise CriticalError(f"Parsing success rate too low: {success_rate:.1%}") │ │    │
│  │  │      elif success_rate < 0.8:  # 50-80% success                   │ │    │
│  │  │          logger.warning(f"Partial parsing success: {success_rate:.1%}") │ │    │
│  │  │          analysis.metadata["parsing_errors"] = errors             │ │    │
│  │  │                                                                   │ │    │
│  │  │      return analysis                                              │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ REPORT GENERATION FAILURES ───────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  def generate_all_reports(self, analysis_results):                │ │    │
│  │  │                                                                   │ │    │
│  │  │      report_status = {                                            │ │    │
│  │  │          "executive_summary": "pending",                          │ │    │
│  │  │          "technical_report": "pending",                           │ │    │
│  │  │          "risk_matrix": "pending",                                │ │    │
│  │  │          "compliance_report": "pending"                           │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      for report_type in report_status.keys():                     │ │    │
│  │  │          try:                                                     │ │    │
│  │  │              output_path = self._generate_report(                 │ │    │
│  │  │                  report_type, analysis_results                   │ │    │
│  │  │              )                                                    │ │    │
│  │  │              report_status[report_type] = "success"               │ │    │
│  │  │              logger.info(f"Generated {report_type}: {output_path}") │ │    │
│  │  │                                                                   │ │    │
│  │  │          except TemplateError as e:                               │ │    │
│  │  │              logger.error(f"Template error in {report_type}: {e}") │ │    │
│  │  │              report_status[report_type] = "template_error"        │ │    │
│  │  │                                                                   │ │    │
│  │  │              # Fallback: Generate simplified version              │ │    │
│  │  │              try:                                                 │ │    │
│  │  │                  fallback_path = self._generate_simple_report(    │ │    │
│  │  │                      report_type, analysis_results               │ │    │
│  │  │                  )                                                │ │    │
│  │  │                  logger.info(f"Fallback report: {fallback_path}") │ │    │
│  │  │                  report_status[report_type] = "fallback_success"  │ │    │
│  │  │              except Exception:                                    │ │    │
│  │  │                  report_status[report_type] = "failed"            │ │    │
│  │  │                                                                   │ │    │
│  │  │          except IOError as e:                                     │ │    │
│  │  │              logger.error(f"IO error in {report_type}: {e}")      │ │    │
│  │  │              report_status[report_type] = "io_error"              │ │    │
│  │  │                                                                   │ │    │
│  │  │          except Exception as e:                                   │ │    │
│  │  │              logger.error(f"Unexpected error in {report_type}: {e}") │ │    │
│  │  │              report_status[report_type] = "unexpected_error"      │ │    │
│  │  │                                                                   │ │    │
│  │  │      # Assessment of Report Generation Success                    │ │    │
│  │  │      success_count = sum(1 for status in report_status.values()   │ │    │
│  │  │                         if status in ["success", "fallback_success"]) │ │    │
│  │  │      total_reports = len(report_status)                           │ │    │
│  │  │                                                                   │ │    │
│  │  │      if success_count == 0:                                       │ │    │
│  │  │          logger.error("All report generation failed")             │ │    │
│  │  │          # Fallback to JSON output only                           │ │    │
│  │  │          return self._generate_json_fallback(analysis_results)    │ │    │
│  │  │                                                                   │ │    │
│  │  │      return report_status                                         │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  PHASE 3: FALLBACK MECHANISMS & GRACEFUL DEGRADATION                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  Degradation Hierarchy (Maintain Critical Functionality)               │    │
│  │                                                                         │    │
│  │  ┌─ FULL FUNCTIONALITY (Ideal State) ─────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  ✅ Rule-based analysis + LLM analysis                             │ │    │
│  │  │  ✅ Interactive Q&A sessions                                       │ │    │
│  │  │  ✅ Comprehensive HTML reports                                     │ │    │
│  │  │  ✅ Multiple output formats (JSON, YAML, HTML)                     │ │    │
│  │  │  ✅ Real-time progress feedback                                    │ │    │
│  │  │  ✅ Configuration hot-reload                                       │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ DEGRADED FUNCTIONALITY (LLM Issues) ──────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  ✅ Rule-based analysis only                                       │ │    │
│  │  │  ⚠️  No interactive Q&A (rule-based responses only)                │ │    │
│  │  │  ✅ Basic HTML reports (no LLM insights section)                   │ │    │
│  │  │  ✅ JSON/YAML output (analysis data only)                          │ │    │
│  │  │  ✅ Progress feedback with LLM status warnings                     │ │    │
│  │  │  ✅ Configuration management                                       │ │    │
│  │  │                                                                   │ │    │
│  │  │  FALLBACK CONTENT GENERATION:                                     │ │    │
│  │  │  ├─ "LLM analysis unavailable - using rule-based only"            │ │    │
│  │  │  ├─ Detailed rule-based findings with enhanced explanations       │ │    │
│  │  │  ├─ Static recommendations based on finding patterns              │ │    │
│  │  │  └─ Links to documentation for manual review                      │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ MINIMAL FUNCTIONALITY (Parsing/Template Issues) ─────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  ✅ Basic rule-based analysis                                      │ │    │
│  │  │  ❌ No interactive features                                        │ │    │
│  │  │  ⚠️  Console output only (no HTML reports)                         │ │    │
│  │  │  ✅ JSON output (raw data structure)                               │ │    │
│  │  │  ⚠️  Minimal progress feedback                                      │ │    │
│  │  │  ⚠️  Basic configuration (no hot-reload)                           │ │    │
│  │  │                                                                   │ │    │
│  │  │  EMERGENCY CONTENT:                                               │ │    │
│  │  │  ├─ Raw analysis data in JSON format                              │ │    │
│  │  │  ├─ Basic console summary with key findings                       │ │    │
│  │  │  ├─ Error log with recovery instructions                          │ │    │
│  │  │  └─ Manual analysis guidance                                      │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  │                                      │                                 │    │
│  │                                      ▼                                 │    │
│  │  ┌─ CRITICAL FAILURE PROTECTION ──────────────────────────────────────┐ │    │
│  │  │                                                                   │ │    │
│  │  │  if critical_error_detected:                                      │ │    │
│  │  │                                                                   │ │    │
│  │  │      # 1. Save Critical Data                                      │ │    │
│  │  │      emergency_output = {                                         │ │    │
│  │  │          "error_info": {                                          │ │    │
│  │  │              "timestamp": datetime.now().isoformat(),             │ │    │
│  │  │              "error_type": type(error).__name__,                  │ │    │
│  │  │              "error_message": str(error),                         │ │    │
│  │  │              "input_directory": str(input_dir),                   │ │    │
│  │  │              "recovery_suggestions": self._get_recovery_suggestions(error) │ │    │
│  │  │          },                                                       │ │    │
│  │  │          "partial_analysis": self._extract_partial_results(),     │ │    │
│  │  │          "system_state": self._capture_system_state()             │ │    │
│  │  │      }                                                            │ │    │
│  │  │                                                                   │ │    │
│  │  │      # 2. Emergency Output                                        │ │    │
│  │  │      emergency_file = output_dir / "emergency_analysis.json"      │ │    │
│  │  │      with open(emergency_file, 'w') as f:                         │ │    │
│  │  │          json.dump(emergency_output, f, indent=2)                 │ │    │
│  │  │                                                                   │ │    │
│  │  │      # 3. User Notification                                       │ │    │
│  │  │      console.print(Panel(                                         │ │    │
│  │  │          f"🚨 CRITICAL ERROR DETECTED\\n\\n"                        │ │    │
│  │  │          f"Error: {error}\\n\\n"                                    │ │    │
│  │  │          f"Emergency data saved to: {emergency_file}\\n\\n"        │ │    │
│  │  │          f"Recovery suggestions:\\n"                               │ │    │
│  │  │          f"{'\\n'.join(recovery_suggestions)}",                      │ │    │
│  │  │          title="Critical Failure",                                │ │    │
│  │  │          style="red"                                              │ │    │
│  │  │      ))                                                           │ │    │
│  │  │                                                                   │ │    │
│  │  │      # 4. Graceful Exit                                           │ │    │
│  │  │      sys.exit(1)                                                  │ │    │
│  │  │                                                                   │ │    │
│  │  └───────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Recovery Metrics and Monitoring

```
┌─── ERROR MONITORING & METRICS DASHBOARD ─────────────────────────────────────────┐
│                                                                                  │
│  ERROR RATE TRACKING                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  class ErrorMetrics:                                                    │    │
│  │                                                                         │    │
│  │      def __init__(self):                                                │    │
│  │          self.error_counts = defaultdict(int)                           │    │
│  │          self.recovery_success_rate = {}                                │    │
│  │          self.fallback_usage = defaultdict(int)                         │    │
│  │          self.critical_failures = []                                    │    │
│  │                                                                         │    │
│  │      def record_error(self, error_type: str, component: str,            │    │
│  │                      recovery_attempted: bool, recovery_success: bool): │    │
│  │                                                                         │    │
│  │          self.error_counts[f"{component}.{error_type}"] += 1            │    │
│  │                                                                         │    │
│  │          if recovery_attempted:                                         │    │
│  │              key = f"{component}.{error_type}"                          │    │
│  │              if key not in self.recovery_success_rate:                  │    │
│  │                  self.recovery_success_rate[key] = []                   │    │
│  │              self.recovery_success_rate[key].append(recovery_success)   │    │
│  │                                                                         │    │
│  │          if not recovery_success and error_type in CRITICAL_ERRORS:     │    │
│  │              self.critical_failures.append({                            │    │
│  │                  "timestamp": datetime.now(),                           │    │
│  │                  "component": component,                                │    │
│  │                  "error_type": error_type                               │    │
│  │              })                                                         │    │
│  │                                                                         │    │
│  │      def get_health_summary(self) -> Dict[str, Any]:                    │    │
│  │          return {                                                       │    │
│  │              "total_errors": sum(self.error_counts.values()),           │    │
│  │              "error_breakdown": dict(self.error_counts),                │    │
│  │              "recovery_rates": {                                        │    │
│  │                  k: sum(v) / len(v) if v else 0                         │    │
│  │                  for k, v in self.recovery_success_rate.items()         │    │
│  │              },                                                         │    │
│  │              "critical_failure_count": len(self.critical_failures),     │    │
│  │              "fallback_usage": dict(self.fallback_usage),               │    │
│  │              "system_health": self._calculate_health_score()            │    │
│  │          }                                                              │    │
│  │                                                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│                                      ▼                                          │
│  HEALTH MONITORING ALERTS                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                         │    │
│  │  ALERT THRESHOLDS:                                                      │    │
│  │                                                                         │    │
│  │  🔴 CRITICAL ALERTS                                                     │    │
│  │  ├─ LLM fallback success rate < 70%                                     │    │
│  │  ├─ Parsing failure rate > 30%                                          │    │
│  │  ├─ Report generation failure rate > 50%                                │    │
│  │  ├─ More than 3 critical failures in 24h                               │    │
│  │  └─ System health score < 0.6                                           │    │
│  │                                                                         │    │
│  │  🟡 WARNING ALERTS                                                      │    │
│  │  ├─ LLM response time > 45 seconds                                      │    │
│  │  ├─ Memory usage > 80%                                                  │    │
│  │  ├─ Disk space < 10% available                                          │    │
│  │  ├─ Configuration reload failures                                       │    │
│  │  └─ Template rendering errors increasing                                │    │
│  │                                                                         │    │
│  │  def check_health_and_alert(self):                                      │    │
│  │      health_summary = self.metrics.get_health_summary()                 │    │
│  │      alerts = []                                                        │    │
│  │                                                                         │    │
│  │      # Critical threshold checks                                        │    │
│  │      if health_summary["system_health"] < 0.6:                          │    │
│  │          alerts.append({                                                │    │
│  │              "level": "CRITICAL",                                       │    │
│  │              "message": f"System health critically low: "               │    │
│  │                        f"{health_summary['system_health']:.2f}",        │    │
│  │              "action": "Investigate error patterns and recovery rates"  │    │
│  │          })                                                             │    │
│  │                                                                         │    │
│  │      for component, rate in health_summary["recovery_rates"].items():   │    │
│  │          if "llm" in component.lower() and rate < 0.7:                  │    │
│  │              alerts.append({                                            │    │
│  │                  "level": "CRITICAL",                                   │    │
│  │                  "message": f"LLM recovery rate low: {rate:.1%}",       │    │
│  │                  "action": "Check LLM provider status and API keys"     │    │
│  │              })                                                         │    │
│  │                                                                         │    │
│  │      return alerts                                                      │    │
│  │                                                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

*[Error Handling and Recovery section completed. Next: Interactive Session Management]*

---

*This document will be expanded with additional technical flow diagrams as development continues.*