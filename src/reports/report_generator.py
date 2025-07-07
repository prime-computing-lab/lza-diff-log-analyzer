"""
Enterprise report generator for LZA diff analysis
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, BaseLoader
from ..analyzers.base import RiskLevel, RiskCategory
from ..formatters.admin_friendly import AdminFriendlyFormatter
from rich.console import Console
from io import StringIO


class StringTemplateLoader(BaseLoader):
    """Custom template loader for string templates"""
    
    def __init__(self, templates: Dict[str, str]):
        self.templates = templates
    
    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        raise FileNotFoundError(f"Template {template} not found")


class AdminReportGenerator:
    """Generate focused reports for cloud administrators performing LZA upgrades"""
    
    def __init__(self, input_dir: Optional[str] = None):
        self.templates = self._get_builtin_templates()
        self.jinja_env = Environment(
            loader=StringTemplateLoader(self.templates),
            autoescape=True
        )
        # Add custom filters
        self.jinja_env.filters['risk_color'] = self._risk_color_filter
        self.jinja_env.filters['format_datetime'] = self._datetime_filter
        self.jinja_env.filters['truncate'] = self._truncate_filter
        
        # Create formatter for data extraction
        console = Console(file=StringIO(), force_terminal=True, width=120)
        self.formatter = AdminFriendlyFormatter(console, input_dir)
    
    def generate_admin_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate cloud administrator focused report"""
        template = self.jinja_env.get_template('admin_report')
        
        # Prepare admin-focused data
        admin_data = self._prepare_admin_data(analysis_results)
        
        return template.render(**admin_data)
    
    
    def save_reports(
        self,
        analysis_results: Dict[str, Any],
        output_dir: Path,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """Save all reports to files"""
        if formats is None:
            formats = ['html']
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Generate admin-focused report
        reports = {
            'admin_report': self.generate_admin_report(analysis_results)
        }
        
        # Save in requested formats
        for report_name, content in reports.items():
            for format_type in formats:
                if format_type == 'html':
                    file_path = output_dir / f"{report_name}.html"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    saved_files[f"{report_name}_html"] = file_path
                elif format_type == 'json':
                    # Save the data used for the report
                    data_path = output_dir / f"{report_name}_data.json"
                    report_data = self._prepare_admin_data(analysis_results)
                    with open(data_path, 'w', encoding='utf-8') as f:
                        json.dump(report_data, f, indent=2, default=str)
                    saved_files[f"{report_name}_json"] = data_path
        
        return saved_files
    
    def _prepare_admin_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for cloud administrator report using terminal formatter"""
        # Extract analysis components
        comprehensive_results = analysis_results
        
        # Handle both dict and object formats for diff_analysis
        if hasattr(analysis_results, 'input_analysis'):
            diff_analysis = analysis_results.input_analysis
        else:
            diff_analysis = analysis_results.get('input_analysis', {})
        
        # Handle both dict and object formats for rule_analysis
        if hasattr(analysis_results, 'rule_based_analysis'):
            rule_analysis = analysis_results.rule_based_analysis or {}
            metadata = analysis_results.metadata or {}
            llm_analysis = analysis_results.llm_analysis or {}
        else:
            rule_analysis = analysis_results.get('rule_based_analysis', {})
            metadata = analysis_results.get('metadata', {})
            llm_analysis = analysis_results.get('llm_analysis', {})
        
        # Get basic metrics using formatter methods
        total_findings = rule_analysis.get('total_findings', 0)
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        
        # Use formatter's version detection
        version_changes = self.formatter._detect_version_changes(diff_analysis)
        
        # Extract key concerns using formatter's logic
        findings = rule_analysis.get('findings', [])
        concern_categories = self.formatter._categorize_concerns(findings)
        high_risk_stacks = self.formatter._get_high_risk_stacks(findings)
        
        # Business impact assessment (mirroring terminal logic)
        has_data_risk = any(f.get('risk_category') == 'data_loss' for f in findings)
        has_security_risk = any(f.get('risk_category') == 'security' for f in findings)
        has_connectivity_risk = any(f.get('risk_category') == 'connectivity' for f in findings)
        has_compliance_risk = any(f.get('risk_category') == 'compliance' for f in findings)
        
        # Overall business risk (matching terminal logic)
        if critical_count > 0:
            business_impact = "HIGH"
            service_impact = "Significant"
        elif high_count > 5:
            business_impact = "MEDIUM"
            service_impact = "Moderate"
        else:
            business_impact = "LOW"
            service_impact = "Minimal"
        
        # Deployment readiness (matching terminal logic)
        if critical_count > 0:
            deployment_readiness = "🔴 NOT READY"
            go_no_go = "NO-GO"
        elif high_count > 5:
            deployment_readiness = "🟡 PROCEED WITH CAUTION"
            go_no_go = "CONDITIONAL GO"
        else:
            deployment_readiness = "🟢 READY TO DEPLOY"
            go_no_go = "GO"
        
        # Get metadata values
        total_stacks = metadata.get('total_stacks', 0)
        total_resources = metadata.get('total_resources_changed', 0)
        total_iam = metadata.get('total_iam_changes', 0)
        
        # Generate deployment checklist using formatter logic
        checklist_items = [
            "Backup current LZA configuration",
            "Verify admin access to all AWS accounts",
            "Notify stakeholders of maintenance window",
            "Prepare rollback procedures"
        ]
        
        if critical_count > 0:
            checklist_items.insert(1, "CRITICAL: Review and resolve critical findings")
        
        if total_iam > 50:
            checklist_items.insert(-1, "Test cross-account access after deployment")
        
        has_network_changes = any('network' in f.get('risk_category', '').lower() for f in findings)
        if has_network_changes:
            checklist_items.insert(-1, "Verify network connectivity paths")
        
        # Extract LLM insights
        llm_insights = {}
        if llm_analysis and isinstance(llm_analysis, dict) and 'analysis_results' in llm_analysis:
            for analysis_type, result in llm_analysis['analysis_results'].items():
                if isinstance(result, dict) and 'content' in result:
                    content = result['content']
                    lines = content.split('\n')
                    key_points = [line.strip() for line in lines if line.strip() and ('•' in line or '-' in line)][:3]
                    llm_insights[analysis_type] = key_points
        
        return {
            'report_title': 'LZA Upgrade Analysis Report ',
            'target_audience': 'Cloud Administrator',
            'generated_at': datetime.now(),
            'analysis_id': self._extract_analysis_id(analysis_results),
            
            # Version information
            'version_changes': version_changes,
            'old_version': version_changes[0] if version_changes else None,
            'new_version': version_changes[1] if version_changes else None,
            
            # High-level metrics (matching terminal)
            'total_stacks': total_stacks,
            'total_changes': total_resources,
            'total_iam_changes': total_iam,
            'overall_risk': rule_analysis.get('overall_risk_level', 'UNKNOWN'),
            'business_impact': business_impact,
            'service_impact': service_impact,
            'deployment_readiness': deployment_readiness,
            'go_no_go_decision': go_no_go,
            
            # Risk counts
            'critical_issues': critical_count,
            'high_risk_issues': high_count,
            'total_risk_findings': total_findings,
            
            # Business areas affected
            'has_security_risk': has_security_risk,
            'has_connectivity_risk': has_connectivity_risk,
            'has_compliance_risk': has_compliance_risk,
            'has_data_risk': has_data_risk,
            
            # Key concerns by category (using formatter logic)
            'concern_categories': concern_categories,
            'high_priority_stacks': high_risk_stacks[:5],  # Top 5 like terminal
            
            # Deployment guidance
            'deployment_recommendation': rule_analysis.get('recommended_action', 'Review required'),
            'deployment_checklist': checklist_items,
            'llm_enabled': metadata.get('llm_enabled', False),
            'llm_insights': llm_insights,
            
            # Risk breakdown for operations
            'security_risks': rule_analysis.get('security_risks', 0),
            'connectivity_risks': rule_analysis.get('connectivity_risks', 0),
            'operational_risks': rule_analysis.get('operational_risks', 0),
            'compliance_risks': rule_analysis.get('compliance_risks', 0),
            'data_loss_risks': rule_analysis.get('data_loss_risks', 0),
            
            # Technical findings for review
            'findings_by_category': concern_categories,
            'technical_recommendations': self._extract_key_recommendations(findings),
            
            # Analysis context
            'is_lza_upgrade': version_changes is not None,
            'finding_volume_assessment': self._assess_finding_volume(total_findings, critical_count, version_changes),
            'iam_percentage': min((total_iam / total_findings * 100) if total_findings > 0 else 0, 100.0)
        }
    
    def _extract_key_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Extract key recommendations from findings"""
        recommendations = []
        for finding in findings:
            if finding.get('risk_level') in ['CRITICAL', 'HIGH']:
                recs = finding.get('recommendations', [])
                # Filter for admin-relevant recommendations
                admin_recs = [rec for rec in recs if any(keyword in rec.lower() for keyword in 
                           ['test', 'deploy', 'monitor', 'validate', 'backup', 'rollback', 'verify'])]
                recommendations.extend(admin_recs[:2])
        return list(set(recommendations))[:8]  # Unique, max 8
    
    def _assess_finding_volume(self, total_findings: int, critical_count: int, version_changes: tuple) -> str:
        """Assess if finding volume is normal for the type of change"""
        if version_changes:
            if total_findings <= 500 and critical_count == 0:
                return "Normal upgrade volume"
            elif total_findings > 500 and critical_count == 0:
                return "Higher than typical volume"
            else:
                return "Critical issues detected"
        else:
            if critical_count > 0:
                return "Critical issues require attention"
            elif total_findings > 100:
                return "Large infrastructure change"
            else:
                return "Moderate change volume"
    
    def _extract_analysis_id(self, analysis_results) -> str:
        """Extract analysis_id from analysis results, handling both object and dict formats"""
        
        # Try to get analysis_id from Pydantic model attribute
        if hasattr(analysis_results, 'analysis_id'):
            analysis_id = getattr(analysis_results, 'analysis_id', None)
            if analysis_id:
                return analysis_id
        
        # Handle dictionary access
        if isinstance(analysis_results, dict):
            analysis_id = analysis_results.get('analysis_id')
            if analysis_id:
                return analysis_id
        
        # Final fallback
        return 'Unknown'
    
    def _risk_color_filter(self, risk_level: str) -> str:
        """Jinja filter for risk level colors"""
        colors = {
            'CRITICAL': '#dc3545',  # Red
            'HIGH': '#fd7e14',      # Orange
            'MEDIUM': '#ffc107',    # Yellow
            'LOW': '#28a745'        # Green
        }
        return colors.get(risk_level.upper(), '#6c757d')
    
    def _datetime_filter(self, dt) -> str:
        """Jinja filter for datetime formatting"""
        if isinstance(dt, str):
            return dt
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def _truncate_filter(self, text: str, length: int = 100) -> str:
        """Jinja filter for text truncation"""
        if len(text) <= length:
            return text
        return text[:length] + '...'
    
    def _get_builtin_templates(self) -> Dict[str, str]:
        """Get built-in HTML templates"""
        return {
            'admin_report': self._get_admin_template()
        }
    
    def _get_admin_template(self) -> str:
        """Cloud administrator focused HTML template mirroring terminal structure"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; color: #333; background: #fafafa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 3px solid #17a2b8; padding-bottom: 20px; margin-bottom: 30px; }
        .section { background: #f8f9fa; border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; border-radius: 6px; }
        .section.executive { border-left-color: #007bff; }
        .section.business { border-left-color: #6f42c1; }
        .section.deployment { border-left-color: #28a745; }
        .section.concerns { border-left-color: #dc3545; }
        .section.actions { border-left-color: #17a2b8; }
        .section.strategic { border-left-color: #20c997; }
        .section.lza-risk { border-left-color: #fd7e14; }
        
        .risk-level { padding: 6px 12px; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 0.9em; }
        .risk-critical { background: #dc3545; color: white; }
        .risk-high { background: #fd7e14; color: white; }
        .risk-medium { background: #ffc107; color: black; }
        .risk-low { background: #28a745; color: white; }
        
        .readiness-ready { color: #28a745; font-weight: bold; }
        .readiness-caution { color: #ffc107; font-weight: bold; }
        .readiness-not-ready { color: #dc3545; font-weight: bold; }
        
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }
        .metric-item { background: white; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6; }
        .metric-label { font-size: 0.85em; color: #6c757d; text-transform: uppercase; margin-bottom: 5px; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #495057; }
        
        .checklist { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .checklist ul { margin: 10px 0; padding-left: 20px; }
        .checklist li { margin: 8px 0; }
        
        .concern-item { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; margin: 10px 0; }
        .concern-number { background: #dc3545; color: white; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.8em; margin-right: 10px; }
        .concern-title { font-weight: bold; color: #495057; }
        .concern-detail { color: #6c757d; font-size: 0.9em; margin: 5px 0; }
        
        .stack-priority { background: white; border: 1px solid #dee2e6; padding: 12px; margin: 8px 0; border-radius: 4px; }
        .priority-high { border-left: 4px solid #dc3545; }
        .priority-medium { border-left: 4px solid #ffc107; }
        .priority-low { border-left: 4px solid #28a745; }
        
        .version-badge { background: #e9ecef; padding: 4px 8px; border-radius: 12px; font-size: 0.85em; margin: 0 4px; }
        .version-old { background: #fff3cd; color: #856404; }
        .version-new { background: #d1edff; color: #004085; }
        
        h2 { color: #007bff; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
        h3 { color: #495057; margin-top: 25px; margin-bottom: 15px; }
        h4 { color: #6c757d; margin-top: 20px; margin-bottom: 10px; }
        
        .alert { padding: 15px; border-radius: 4px; margin: 15px 0; }
        .alert-success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
        .alert-danger { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        
        .badge { display: inline-block; padding: 0.25em 0.6em; font-size: 0.75em; font-weight: 700; line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: 0.25rem; }
        .badge-success { background-color: #28a745; color: white; }
        .badge-warning { background-color: #ffc107; color: black; }
        .badge-danger { background-color: #dc3545; color: white; }
        
        .expand-section { cursor: pointer; }
        .expand-section:hover { background-color: #e9ecef; }
        .expandable-content { display: none; margin-top: 15px; }
        .expandable-content.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 {{ report_title }}</h1>
            <p><strong>Generated:</strong> {{ generated_at | format_datetime }}</p>
            <p><strong>Analysis ID:</strong> {{ analysis_id }}</p>
            {% if is_lza_upgrade %}
                <p><strong>LZA Platform Upgrade:</strong> 
                    <span class="version-badge version-old">{{ old_version }}</span> → 
                    <span class="version-badge version-new">{{ new_version }}</span>
                </p>
            {% endif %}
        </div>

        <!-- Executive Summary -->
        <div class="section executive">
            <h2>🎯 Executive Summary</h2>
            {% if is_lza_upgrade %}
                <div class="alert alert-info" style="background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #0c5460;">🚀 LZA Platform Upgrade</h4>
                    <p style="margin: 0; font-size: 1.1em;">
                        <strong>Version {{ old_version }}</strong> → <strong>Version {{ new_version }}</strong>
                    </p>
                </div>
            {% endif %}
            <div class="metric-grid">
                {% if is_lza_upgrade %}
                <div class="metric-item" style="border-left: 4px solid #17a2b8;">
                    <div class="metric-label">LZA Upgrade</div>
                    <div class="metric-value" style="font-size: 1.2em;">{{ old_version }} → {{ new_version }}</div>
                </div>
                {% endif %}
                <div class="metric-item">
                    <div class="metric-label">CloudFormation Stacks</div>
                    <div class="metric-value">{{ total_stacks }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Resource Changes</div>
                    <div class="metric-value">{{ total_changes }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">IAM Updates</div>
                    <div class="metric-value">{{ total_iam_changes }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Risk Findings</div>
                    <div class="metric-value">{{ total_risk_findings }}</div>
                </div>
            </div>
            
            <p><strong>Risk Assessment:</strong> <span class="risk-level risk-{{ overall_risk.lower() }}">{{ overall_risk }}</span></p>
            {% if critical_issues > 0 or high_risk_issues > 0 %}
                <p><strong>Priority Issues:</strong> {{ critical_issues }} critical, {{ high_risk_issues }} high-risk</p>
            {% endif %}
            
            <div class="alert alert-{{ 'success' if finding_volume_assessment == 'Normal upgrade volume' else 'warning' if 'typical' in finding_volume_assessment else 'danger' }}">
                <strong>Assessment:</strong> {{ finding_volume_assessment }}
            </div>
        </div>

        <!-- Business Impact Assessment -->
        <div class="section business">
            <h2>💼 Business Impact Assessment</h2>
            <p><strong>Overall Business Risk:</strong> 
                <span class="badge badge-{{ 'danger' if business_impact == 'HIGH' else 'warning' if business_impact == 'MEDIUM' else 'success' }}">
                    {{ business_impact }}
                </span>
            </p>
            <p><strong>Service Availability Impact:</strong> {{ service_impact }}</p>
            
            <h4>Potential Business Areas Affected:</h4>
            <ul>
                {% if has_security_risk %}
                <li>🔒 <strong>Security Posture</strong> - Access controls and permissions updating</li>
                {% endif %}
                {% if has_connectivity_risk %}
                <li>🌐 <strong>Network Connectivity</strong> - Hub-spoke and cross-account communications</li>
                {% endif %}
                {% if has_compliance_risk %}
                <li>📋 <strong>Compliance & Audit</strong> - Logging and governance controls</li>
                {% endif %}
                {% if has_data_risk %}
                <li>💾 <strong>Data Protection</strong> - Backup and encryption systems</li>
                {% endif %}
                {% if not (has_security_risk or has_connectivity_risk or has_compliance_risk or has_data_risk) %}
                <li>✅ No significant business-critical systems affected</li>
                {% endif %}
            </ul>
        </div>

        <!-- Deployment Readiness -->
        <div class="section deployment">
            <h2>🚀 Deployment Readiness</h2>
            <p><strong>Status:</strong> <span class="readiness-{{ 'ready' if '🟢' in deployment_readiness else 'caution' if '🟡' in deployment_readiness else 'not-ready' }}">{{ deployment_readiness }}</span></p>
            <p><strong>Go/No-Go Decision:</strong> 
                <span class="badge badge-{{ 'success' if go_no_go_decision == 'GO' else 'warning' if 'CONDITIONAL' in go_no_go_decision else 'danger' }}">
                    {{ go_no_go_decision }}
                </span>
            </p>
            
            <div class="checklist">
                <h4>Pre-Deployment Checklist:</h4>
                <ul>
                    {% for item in deployment_checklist %}
                    <li>□ {{ item }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>

        <!-- Key Concerns -->
        {% if concern_categories %}
        <div class="section concerns">
            <h2>⚠️ Key Concerns (Requires Your Review)</h2>
            {% set concern_count = [0] %}
            {% for category, findings in concern_categories.items() %}
                {% if findings %}
                    {% if concern_count.append(concern_count.pop() + 1) %}{% endif %}
                    <div class="concern-item">
                        <span class="concern-number">{{ concern_count[0] }}</span>
                        <span class="concern-title">
                            {% if category == 'iam_changes' %}IAM Permission Changes{% endif %}
                            {% if category == 'resource_deletions' %}Resource Deletions{% endif %}
                            {% if category == 'security_configs' %}Security Configuration Changes{% endif %}
                            {% if category == 'network_changes' %}Network Configuration Changes{% endif %}
                        </span>
                        <span class="badge badge-warning">{{ findings|length }} findings</span>
                        <div class="concern-detail">
                            {% if category == 'iam_changes' %}
                                Why: Roles and policies are being modified<br>
                                Action: Review cross-account access and trust relationships
                            {% elif category == 'resource_deletions' %}
                                Why: Resources are being removed from stacks<br>
                                Action: Verify no dependencies or data loss
                            {% elif category == 'security_configs' %}
                                Why: Security-related settings are being updated<br>
                                Action: Review impact on security posture
                            {% elif category == 'network_changes' %}
                                Why: Network settings or connectivity may be affected<br>
                                Action: Test connectivity after deployment
                            {% endif %}
                        </div>
                    </div>
                {% endif %}
            {% endfor %}
        </div>
        {% endif %}

        <!-- High Priority Stacks -->
        {% if high_priority_stacks %}
        <div class="section">
            <h2>🎯 High-Priority Stacks for Review</h2>
            {% for stack in high_priority_stacks %}
            <div class="stack-priority priority-high">
                <strong>{{ stack }}</strong> - Requires immediate admin review
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Strategic Recommendations -->
        <div class="section strategic">
            <h2>🎯 Strategic Recommendations</h2>
            {% if technical_recommendations %}
            <h4>Immediate Actions (Next 24-48 Hours):</h4>
            <ul>
                {% for rec in technical_recommendations[:4] %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            <h4>Key Validation Questions:</h4>
            <ul>
                <li>Can your workloads continue operating normally after these infrastructure changes?</li>
                <li>Are all cross-account access patterns maintained?</li>
                <li>Will security and compliance requirements still be met?</li>
            </ul>
        </div>

        <!-- LZA Risk Assessment -->
        {% if is_lza_upgrade %}
        <div class="section lza-risk">
            <h2>🎯 LZA Risk Assessment</h2>
            <p><strong>Pattern Assessment:</strong> {{ finding_volume_assessment }}</p>
            <p><strong>IAM Changes:</strong> {{ iam_percentage|round }}% of findings ({{ total_iam_changes }} IAM updates)</p>
            
            <div class="alert alert-{{ 'success' if iam_percentage >= 60 else 'warning' }}">
                {% if iam_percentage >= 60 %}
                ✅ <strong>Normal IAM Pattern:</strong> IAM changes represent typical cross-account management updates for LZA
                {% else %}
                ⚠️ <strong>Atypical IAM Pattern:</strong> Lower than typical IAM percentage for LZA upgrades
                {% endif %}
            </div>
            
            <h4>LZA Testing Priority:</h4>
            <ol>
                <li>Cross-account access (Log Archive, Audit accounts)</li>
                <li>Centralized logging functionality</li>
                <li>Security service operations</li>
                <li>Network connectivity between accounts</li>
                <li>Control Tower integration</li>
            </ol>
        </div>
        {% endif %}

        <!-- Technical Reference -->
        <div class="section">
            <h2>📊 Technical Reference</h2>
            <h4>Risk Level Breakdown:</h4>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">Critical</div>
                    <div class="metric-value risk-critical">{{ critical_issues }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">High</div>
                    <div class="metric-value risk-high">{{ high_risk_issues }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Security Risks</div>
                    <div class="metric-value">{{ security_risks }}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Connectivity Risks</div>
                    <div class="metric-value">{{ connectivity_risks }}</div>
                </div>
            </div>
            
            <p><strong>LLM Enhancement:</strong> {{ '✅ Enabled' if llm_enabled else '❌ Disabled' }}</p>
            
            {% if llm_enabled and llm_insights %}
            <h4>AI-Enhanced Analysis:</h4>
            {% for analysis_type, insights in llm_insights.items() %}
            <div class="expand-section" onclick="toggleExpand('{{ analysis_type }}')">
                <h5>{{ analysis_type.replace('_', ' ').title() }} ▼</h5>
            </div>
            <div id="{{ analysis_type }}" class="expandable-content">
                <ul>
                {% for insight in insights %}
                    <li>{{ insight }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endfor %}
            {% endif %}
        </div>
    </div>

    <script>
        function toggleExpand(id) {
            const content = document.getElementById(id);
            content.classList.toggle('show');
        }
    </script>
</body>
</html>
        '''
    
