"""
Cloud Administrator-friendly output formatter for LZA diff analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from collections import defaultdict


class AdminFriendlyFormatter:
    """Formats analysis results in a cloud administrator-friendly way"""
    
    def __init__(self, console: Console, input_dir: Optional[str] = None):
        self.console = console
        self.input_dir = input_dir
        self.file_mapping = {}
        
        # Load file mapping if input_dir is provided
        if input_dir:
            try:
                from pathlib import Path
                from ..parsers.file_utils import FileManager
                self.file_mapping = FileManager.get_diff_file_mapping(Path(input_dir))
            except Exception:
                pass
    
    def format_summary(self, comprehensive_results, diff_analysis, enable_llm: bool):
        """Format the analysis summary for cloud administrators"""
        
        # Extract key information
        if hasattr(comprehensive_results, 'rule_based_analysis'):
            rule_analysis = comprehensive_results.rule_based_analysis
            metadata = comprehensive_results.metadata
            llm_analysis = comprehensive_results.llm_analysis
            input_analysis = comprehensive_results.input_analysis
        else:
            # Handle backward compatibility with dictionary format
            if hasattr(comprehensive_results, 'get'):
                rule_analysis = comprehensive_results.get("rule_based_analysis", {})
                metadata = comprehensive_results.get("metadata", {})
                llm_analysis = comprehensive_results.get("llm_analysis")
            else:
                # Handle Pydantic model format
                rule_analysis = getattr(comprehensive_results, 'rule_based_analysis', {})
                metadata = getattr(comprehensive_results, 'metadata', {})
                llm_analysis = getattr(comprehensive_results, 'llm_analysis', None)
            input_analysis = diff_analysis
        
        # Print executive summary with strategic insights
        self._print_executive_summary(input_analysis, rule_analysis, metadata)
        
        # Print business impact assessment
        self._print_business_impact_assessment(rule_analysis, input_analysis, metadata)
        
        # Print deployment readiness assessment
        self._print_deployment_readiness(rule_analysis, input_analysis, metadata)
        
        # Print key concerns
        self._print_key_concerns(rule_analysis, input_analysis, metadata)
        
        # Print immediate actions
        self._print_immediate_actions(rule_analysis, input_analysis, metadata)
        
        # Print strategic recommendations
        self._print_strategic_recommendations(rule_analysis, input_analysis, metadata)
        
        # Print context and reassurance
        self._print_context(input_analysis, rule_analysis, metadata)
        
        # Print LZA-specific risk assessment
        self._print_lza_risk_assessment(rule_analysis, input_analysis, metadata)
        
        # Print technical details for reference
        self._print_technical_reference(rule_analysis, metadata, enable_llm, comprehensive_results)
    
    def _print_executive_summary(self, input_analysis, rule_analysis, metadata=None):
        """Print enhanced executive summary with strategic insights"""
        
        # Detect LZA version upgrade
        version_changes = self._detect_version_changes(input_analysis)
        risk_level = rule_analysis.get('overall_risk_level', 'UNKNOWN')
        total_findings = rule_analysis.get('total_findings', 0)
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        
        summary_text = f"🎯 [bold blue]EXECUTIVE SUMMARY[/bold blue]\n"
        
        # Get totals from metadata first, then fallback to input_analysis
        if metadata:
            total_stacks = metadata.get('total_stacks', 0)
            total_resources = metadata.get('total_resources_changed', 0)
            total_iam = metadata.get('total_iam_changes', 0)
        else:
            total_stacks = getattr(input_analysis, 'total_stacks', 0)
            total_resources = getattr(input_analysis, 'total_resources_changed', 0)
            total_iam = getattr(input_analysis, 'total_iam_changes', 0)
        
        if version_changes:
            old_ver, new_ver = version_changes
            summary_text += f"**LZA Platform Upgrade:** [yellow]{old_ver}[/yellow] → [green]{new_ver}[/green]\n"
            summary_text += f"**Scope:** [bold]{total_stacks}[/bold] stacks across multiple AWS accounts\n"
        else:
            summary_text += f"**Infrastructure Change:** [bold]{total_stacks}[/bold] CloudFormation stacks affected\n"
        
        summary_text += f"**Change Volume:** {total_resources} resources, {total_iam} IAM updates\n"
        
        # Risk assessment with color coding
        risk_color = {
            "LOW": "green", "MEDIUM": "yellow", "HIGH": "orange3", "CRITICAL": "red"
        }.get(risk_level, "white")
        
        summary_text += f"**Risk Assessment:** [{risk_color}]{risk_level}[/{risk_color}] - {total_findings} findings"
        
        if critical_count > 0 or high_count > 0:
            summary_text += f" ([red]{critical_count} critical[/red], [orange3]{high_count} high[/orange3])"
        
        # Strategic assessment
        summary_text += f"\n\n**Strategic Assessment:**\n"
        if version_changes and total_findings > 300:
            summary_text += "✓ Finding volume typical for major LZA upgrades\n"
            summary_text += "✓ Most changes are routine platform maintenance\n"
        elif critical_count == 0 and high_count < 5:
            summary_text += "✓ Low operational risk - primarily routine updates\n"
        elif critical_count > 0:
            summary_text += "⚠ Critical issues require executive attention\n"
        
        if input_analysis.total_iam_changes > 100:
            summary_text += "• Significant IAM restructuring - review trust relationships\n"
        
        panel = Panel(summary_text, expand=False, border_style="blue", title="Strategic Overview")
        self.console.print(panel)
        self.console.print()
    
    def _print_business_impact_assessment(self, rule_analysis, input_analysis, metadata=None):
        """Print business impact assessment for executives"""
        
        findings = rule_analysis.get("findings", [])
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        
        # Assess business impact categories
        has_data_risk = any(f.get('risk_category') == 'data_loss' for f in findings)
        has_security_risk = any(f.get('risk_category') == 'security' for f in findings)
        has_connectivity_risk = any(f.get('risk_category') == 'connectivity' for f in findings)
        has_compliance_risk = any(f.get('risk_category') == 'compliance' for f in findings)
        
        self.console.print("💼 [bold magenta]BUSINESS IMPACT ASSESSMENT[/bold magenta]")
        
        impact_text = ""
        
        # Overall business risk
        if critical_count > 0:
            impact_text += "**Overall Business Risk:** [red]HIGH[/red] - Immediate executive attention required\n"
        elif high_count > 5:
            impact_text += "**Overall Business Risk:** [yellow]MEDIUM[/yellow] - Careful planning needed\n"
        else:
            impact_text += "**Overall Business Risk:** [green]LOW[/green] - Standard operational change\n"
        
        # Service availability impact
        service_impact = "Minimal" if (critical_count == 0 and high_count < 3) else "Moderate" if critical_count == 0 else "Significant"
        color = "green" if service_impact == "Minimal" else "yellow" if service_impact == "Moderate" else "red"
        impact_text += f"**Service Availability Impact:** [{color}]{service_impact}[/{color}]\n"
        
        # Specific business areas
        impact_text += "\n**Potential Business Areas Affected:**\n"
        
        if has_security_risk:
            impact_text += "🔒 **Security Posture** - Access controls and permissions updating\n"
        if has_connectivity_risk:
            impact_text += "🌐 **Network Connectivity** - Hub-spoke and cross-account communications\n"
        if has_compliance_risk:
            impact_text += "📋 **Compliance & Audit** - Logging and governance controls\n"
        if has_data_risk:
            impact_text += "💾 **Data Protection** - Backup and encryption systems\n"
        
        if not any([has_security_risk, has_connectivity_risk, has_compliance_risk, has_data_risk]):
            impact_text += "✅ No significant business-critical systems affected\n"
        
        # Downtime assessment
        impact_text += f"\n**Expected Downtime:** "
        if critical_count > 0:
            impact_text += "[red]Potential service interruption[/red] - Plan maintenance window"
        elif high_count > 3:
            impact_text += "[yellow]Brief service impact possible[/yellow] - Monitor deployment"
        else:
            impact_text += "[green]Zero downtime expected[/green] - Background updates only"
        
        panel = Panel(impact_text, expand=False, border_style="magenta")
        self.console.print(panel)
        self.console.print()
    
    def _print_deployment_readiness(self, rule_analysis, input_analysis, metadata=None):
        """Print deployment readiness checklist"""
        
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        findings = rule_analysis.get("findings", [])
        
        self.console.print("🚀 [bold green]DEPLOYMENT READINESS[/bold green]")
        
        # Overall readiness assessment
        if critical_count > 0:
            readiness = "🔴 NOT READY"
            readiness_color = "red"
        elif high_count > 5:
            readiness = "🟡 PROCEED WITH CAUTION"
            readiness_color = "yellow"
        else:
            readiness = "🟢 READY TO DEPLOY"
            readiness_color = "green"
        
        readiness_text = f"**Status:** [{readiness_color}]{readiness}[/{readiness_color}]\n\n"
        
        # Pre-deployment checklist
        readiness_text += "**Pre-Deployment Checklist:**\n"
        
        # Required actions based on findings
        checklist_items = [
            "□ Backup current LZA configuration",
            "□ Verify admin access to all AWS accounts",
            "□ Notify stakeholders of maintenance window",
            "□ Prepare rollback procedures"
        ]
        
        if critical_count > 0:
            checklist_items.insert(1, "□ [red]CRITICAL: Review and resolve critical findings[/red]")
        
        # Get total IAM changes
        total_iam = metadata.get('total_iam_changes', 0) if metadata else getattr(input_analysis, 'total_iam_changes', 0)
        
        if total_iam > 50:
            checklist_items.insert(-1, "□ Test cross-account access after deployment")
        
        has_network_changes = any('network' in f.get('risk_category', '').lower() for f in findings)
        if has_network_changes:
            checklist_items.insert(-1, "□ Verify network connectivity paths")
        
        for item in checklist_items:
            readiness_text += f"{item}\n"
        
        # Timing recommendation
        readiness_text += f"\n**Recommended Timing:**\n"
        if critical_count > 0:
            readiness_text += "⏸️  Delay deployment until critical issues resolved\n"
        elif high_count > 3:
            readiness_text += "🕒 Schedule during low-traffic hours with full team support\n"
        else:
            readiness_text += "✅ Can proceed during standard maintenance window\n"
        
        # Go/No-Go decision framework
        readiness_text += f"\n**Go/No-Go Decision:**\n"
        if critical_count == 0 and high_count <= 5:
            readiness_text += "✅ [green]GO[/green] - Acceptable risk profile for deployment\n"
        elif critical_count == 0:
            readiness_text += "⚠️  [yellow]CONDITIONAL GO[/yellow] - Enhanced monitoring required\n"
        else:
            readiness_text += "🛑 [red]NO-GO[/red] - Resolve critical issues first\n"
        
        panel = Panel(readiness_text, expand=False, border_style="green")
        self.console.print(panel)
        self.console.print()
    
    def _print_key_concerns(self, rule_analysis, input_analysis, metadata=None):
        """Print key concerns that require administrator attention"""
        
        findings = rule_analysis.get("findings", [])
        concern_categories = self._categorize_concerns(findings)
        
        self.console.print("⚠️  [bold red]KEY CONCERNS[/bold red] (Requires Your Review):")
        
        priority_order = ["iam_changes", "resource_deletions", "security_configs", "network_changes"]
        
        concern_count = 0
        for category in priority_order:
            if category in concern_categories and concern_categories[category]:
                concern_count += 1
                count = len(concern_categories[category])
                
                # Get affected stack files for this category
                affected_stacks = self._get_affected_stack_files(concern_categories[category], input_analysis)
                
                if category == "iam_changes":
                    self.console.print(f"{concern_count}. [yellow]IAM Permission Changes[/yellow] ({count} findings)")
                    self.console.print("   └─ [dim]Why:[/dim] Roles and policies are being modified")
                    self.console.print("   └─ [dim]Action:[/dim] Review cross-account access and trust relationships")
                    if affected_stacks:
                        self.console.print(f"   └─ [dim]Files to review:[/dim] {', '.join(affected_stacks[:3])}")
                        if len(affected_stacks) > 3:
                            self.console.print(f"   └─ [dim]...and {len(affected_stacks)-3} more files[/dim]")
                    
                elif category == "resource_deletions":
                    self.console.print(f"{concern_count}. [red]Resource Deletions[/red] ({count} findings)")  
                    self.console.print("   └─ [dim]Why:[/dim] Resources are being removed from stacks")
                    self.console.print("   └─ [dim]Action:[/dim] Verify no dependencies or data loss")
                    if affected_stacks:
                        self.console.print(f"   └─ [dim]Files to review:[/dim] {', '.join(affected_stacks[:3])}")
                        if len(affected_stacks) > 3:
                            self.console.print(f"   └─ [dim]...and {len(affected_stacks)-3} more files[/dim]")
                    
                elif category == "security_configs":
                    self.console.print(f"{concern_count}. [orange3]Security Configuration Changes[/orange3] ({count} findings)")
                    self.console.print("   └─ [dim]Why:[/dim] Security-related settings are being updated")
                    self.console.print("   └─ [dim]Action:[/dim] Review impact on security posture")
                    if affected_stacks:
                        self.console.print(f"   └─ [dim]Files to review:[/dim] {', '.join(affected_stacks[:3])}")
                        if len(affected_stacks) > 3:
                            self.console.print(f"   └─ [dim]...and {len(affected_stacks)-3} more files[/dim]")
                    
                elif category == "network_changes":
                    self.console.print(f"{concern_count}. [cyan]Network Configuration Changes[/cyan] ({count} findings)")
                    self.console.print("   └─ [dim]Why:[/dim] Network settings or connectivity may be affected")
                    self.console.print("   └─ [dim]Action:[/dim] Test connectivity after deployment")
                    if affected_stacks:
                        self.console.print(f"   └─ [dim]Files to review:[/dim] {', '.join(affected_stacks[:3])}")
                        if len(affected_stacks) > 3:
                            self.console.print(f"   └─ [dim]...and {len(affected_stacks)-3} more files[/dim]")
                
                self.console.print()
        
        if concern_count == 0:
            self.console.print("✅ [green]No high-priority concerns detected![/green]")
            self.console.print()
    
    def _print_immediate_actions(self, rule_analysis, input_analysis, metadata=None):
        """Print immediate actions checklist"""
        
        findings = rule_analysis.get("findings", [])
        high_risk_stacks = self._get_high_risk_stacks(findings)
        
        self.console.print("🎯 [bold green]IMMEDIATE ACTIONS[/bold green]:")
        
        actions = [
            "Test changes in non-production environment first",
            "Review IAM changes for unintended privilege escalation", 
            "Validate automation scripts work with updated parameters",
            "Backup current configurations before proceeding"
        ]
        
        if high_risk_stacks:
            actions.append(f"Focus on high-risk stacks: {', '.join(high_risk_stacks[:3])}")
            if len(high_risk_stacks) > 3:
                actions.append(f"...and {len(high_risk_stacks)-3} other stacks")
        
        for action in actions:
            self.console.print(f"□ {action}")
        
        # Add section for diff files to review
        if self.file_mapping:
            high_risk_files = self._get_prioritized_files(findings)
            if high_risk_files:
                self.console.print("\n📁 [bold yellow]Priority Diff Files to Review:[/bold yellow]")
                for i, (file_name, reason) in enumerate(high_risk_files[:5], 1):
                    self.console.print(f"{i}. {file_name} - {reason}")
                if len(high_risk_files) > 5:
                    self.console.print(f"   ...and {len(high_risk_files)-5} more files")
        
        self.console.print()
    
    def _print_strategic_recommendations(self, rule_analysis, input_analysis, metadata=None):
        """Print strategic recommendations for executives"""
        
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        findings = rule_analysis.get("findings", [])
        version_changes = self._detect_version_changes(input_analysis)
        
        self.console.print("🎯 [bold cyan]STRATEGIC RECOMMENDATIONS[/bold cyan]")
        
        recommendations_text = ""
        
        # Immediate recommendations
        recommendations_text += "**Immediate Actions (Next 24-48 Hours):**\n"
        
        if critical_count > 0:
            recommendations_text += "1. [red]PRIORITY 1[/red]: Address all critical findings before proceeding\n"
            recommendations_text += "2. Convene emergency change review board\n"
            recommendations_text += "3. Prepare detailed rollback procedures\n"
        elif high_count > 5:
            recommendations_text += "1. [yellow]Enhanced Review[/yellow]: Deep-dive into high-risk changes\n"
            recommendations_text += "2. Extend testing phase by 24-48 hours\n"
            recommendations_text += "3. Increase deployment team availability\n"
        else:
            recommendations_text += "1. [green]Standard Process[/green]: Proceed with normal deployment cadence\n"
            recommendations_text += "2. Execute standard pre-deployment tests\n"
            recommendations_text += "3. Monitor deployment progress normally\n"
        
        # Medium-term strategy
        recommendations_text += "\n**Medium-Term Strategy (Next 1-2 Weeks):**\n"
        
        if version_changes:
            recommendations_text += "• Deploy in phased approach: Non-prod → Staging → Production\n"
            recommendations_text += "• Validate each phase before proceeding to next\n"
            recommendations_text += "• Monitor for 48-72 hours post-deployment\n"
        
        # Get total IAM changes
        total_iam = metadata.get('total_iam_changes', 0) if metadata else getattr(input_analysis, 'total_iam_changes', 0)
        
        if total_iam > 100:
            recommendations_text += "• Conduct IAM access audit 1 week post-deployment\n"
            recommendations_text += "• Verify all cross-account integrations are functional\n"
        
        has_network_findings = any('network' in f.get('risk_category', '').lower() for f in findings)
        if has_network_findings:
            recommendations_text += "• Perform comprehensive network connectivity testing\n"
            recommendations_text += "• Update network documentation and runbooks\n"
        
        # Long-term improvements
        recommendations_text += "\n**Long-Term Improvements (Next 1-3 Months):**\n"
        
        if critical_count > 2 or high_count > 10:
            recommendations_text += "• Review and enhance change management processes\n"
            recommendations_text += "• Implement automated pre-deployment validation\n"
            recommendations_text += "• Consider additional staging environments\n"
        
        recommendations_text += "• Establish automated monitoring for LZA health\n"
        recommendations_text += "• Create incident response playbook for LZA issues\n"
        
        if version_changes:
            old_ver, new_ver = version_changes
            recommendations_text += f"• Plan next upgrade cycle ({new_ver} → next version)\n"
        
        # Success metrics
        recommendations_text += "\n**Success Metrics to Track:**\n"
        recommendations_text += "• Zero unplanned service outages\n"
        recommendations_text += "• All cross-account functionality operational\n"
        recommendations_text += "• No security or compliance violations\n"
        recommendations_text += "• Deployment completed within planned window\n"
        
        panel = Panel(recommendations_text, expand=False, border_style="cyan", title="Executive Action Plan")
        self.console.print(panel)
        self.console.print()
    
    def _print_context(self, input_analysis, rule_analysis, metadata=None):
        """Print context and reassurance"""
        
        findings = rule_analysis.get("findings", [])
        total_findings = len(findings)
        
        context_text = "💡 [bold cyan]CONTEXT[/bold cyan]\n"
        
        # Detect if this looks like an LZA upgrade
        version_changes = self._detect_version_changes(input_analysis)
        if version_changes:
            context_text += f"This appears to be a standard LZA upgrade. High finding counts ({total_findings}) are "
            context_text += "normal due to IAM management complexity and version parameter updates.\n\n"
            context_text += "Focus on the prioritized items above rather than the total count. "
            context_text += "Most findings are informational updates that don't require action."
        else:
            if total_findings > 100:
                context_text += f"Large number of findings ({total_findings}) suggests significant infrastructure changes. "
                context_text += "This is common with major deployments or configuration updates.\n\n"
                context_text += "Focus on security and IAM-related changes first."
            else:
                context_text += f"Moderate number of findings ({total_findings}) indicates routine changes. "
                context_text += "Review the key concerns above to ensure nothing unexpected."
        
        panel = Panel(context_text, expand=False, border_style="cyan")
        self.console.print(panel)
        self.console.print()
    
    def _print_lza_risk_assessment(self, rule_analysis, input_analysis, metadata=None):
        """Print LZA-specific risk assessment and upgrade patterns"""
        
        total_findings = rule_analysis.get('total_findings', 0)
        critical_count = rule_analysis.get('critical_count', 0)
        high_count = rule_analysis.get('high_count', 0)
        version_changes = self._detect_version_changes(input_analysis)
        
        # Get total IAM changes
        total_iam = metadata.get('total_iam_changes', 0) if metadata else getattr(input_analysis, 'total_iam_changes', 0)
        
        self.console.print("🎯 [bold blue]LZA RISK ASSESSMENT[/bold blue]")
        
        assessment_text = ""
        
        # LZA upgrade pattern recognition
        if version_changes:
            old_ver, new_ver = version_changes
            assessment_text += f"**LZA Upgrade Pattern Analysis ({old_ver} → {new_ver}):**\n"
            
            # Typical upgrade patterns
            assessment_text += "**Normal upgrade expectations:**\n"
            assessment_text += "• 200-500 findings typical for major LZA upgrades\n"
            assessment_text += "• ~70% IAM adjustments (expected for cross-account management)\n"
            assessment_text += "• SSM parameter updates (routine version changes)\n"
            assessment_text += "• Service role permission adjustments for new features\n\n"
            
            # Assessment of current upgrade
            if total_findings <= 500 and critical_count == 0:
                assessment_text += "✅ **Pattern Assessment:** [green]Normal upgrade volume[/green]\n"
            elif total_findings > 500 and critical_count == 0:
                assessment_text += "⚠️ **Pattern Assessment:** [yellow]Higher than typical volume[/yellow]\n"
            else:
                assessment_text += "🔴 **Pattern Assessment:** [red]Critical issues detected[/red]\n"
                
            # IAM change assessment
            iam_percentage = (total_iam / total_findings * 100) if total_findings > 0 else 0
            if iam_percentage >= 60:
                assessment_text += f"✅ **IAM Changes:** [green]{iam_percentage:.0f}% of findings[/green] (typical for LZA)\n"
            else:
                assessment_text += f"⚠️ **IAM Changes:** [yellow]{iam_percentage:.0f}% of findings[/yellow] (lower than typical)\n"
        else:
            assessment_text += "**Infrastructure Change Analysis:**\n"
            assessment_text += f"• {total_findings} findings detected in CloudFormation changes\n"
            assessment_text += f"• {total_iam} IAM-related modifications\n\n"
        
        # Risk prioritization guidance
        assessment_text += "\n**LZA Risk Prioritization:**\n"
        
        # Critical areas for LZA
        assessment_text += "🔴 **Immediate attention required:**\n"
        assessment_text += "  • Resource deletions (potential data loss)\n"
        assessment_text += "  • Security service configuration changes\n"
        assessment_text += "  • Network connectivity modifications\n"
        assessment_text += "  • Cross-account IAM trust relationship changes\n\n"
        
        assessment_text += "🟡 **Enhanced review needed:**\n"
        assessment_text += "  • New IAM permissions or policies\n"
        assessment_text += "  • Logging and audit configuration changes\n"
        assessment_text += "  • Control Tower integration updates\n\n"
        
        assessment_text += "🟢 **Standard review (lower priority):**\n"
        assessment_text += "  • SSM parameter version updates\n"
        assessment_text += "  • CloudFormation template metadata changes\n"
        assessment_text += "  • Service role permission adjustments\n\n"
        
        # Current analysis focus areas
        assessment_text += "**Your Analysis Focus Areas:**\n"
        
        if critical_count > 0:
            assessment_text += f"🚨 **CRITICAL:** {critical_count} critical findings require immediate resolution\n"
        
        if high_count > 0:
            assessment_text += f"⚠️ **HIGH PRIORITY:** {high_count} high-risk changes need detailed review\n"
        
        # Calculate routine vs concerning changes
        routine_findings = total_findings - critical_count - high_count
        if routine_findings > 0:
            assessment_text += f"📝 **ROUTINE:** {routine_findings} standard findings (likely routine maintenance)\n"
        
        # Key validation question
        assessment_text += f"\n**Key Question for LZA Upgrades:**\n"
        assessment_text += f"*Can your workloads continue operating normally after these infrastructure changes?*\n"
        
        # Testing guidance specific to LZA
        assessment_text += f"\n**LZA Testing Priority:**\n"
        assessment_text += f"1. Cross-account access (Log Archive, Audit accounts)\n"
        assessment_text += f"2. Centralized logging functionality\n"
        assessment_text += f"3. Security service operations\n"
        assessment_text += f"4. Network connectivity between accounts\n"
        assessment_text += f"5. Control Tower integration\n"
        
        panel = Panel(assessment_text, expand=False, border_style="blue", title="LZA Upgrade Risk Context")
        self.console.print(panel)
        self.console.print()
    
    def _print_technical_reference(self, rule_analysis, metadata, enable_llm, comprehensive_results=None):
        """Print technical details for reference"""
        
        findings = rule_analysis.get("findings", [])
        risk_counts = self._count_by_risk_level(findings)
        
        self.console.print("📊 [bold]Technical Reference[/bold] (for detailed analysis):")
        
        # Risk level breakdown
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Risk Level", style="dim")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right", style="dim")
        
        total = sum(risk_counts.values()) or 1
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = risk_counts.get(level, 0)
            percentage = f"{(count/total)*100:.1f}%"
            color = {"CRITICAL": "red", "HIGH": "orange3", "MEDIUM": "yellow", "LOW": "green"}.get(level, "white")
            table.add_row(f"[{color}]{level}[/{color}]", str(count), percentage)
        
        self.console.print(table)
        self.console.print()
        
        # Analysis details
        analyzers = metadata.get('analyzers_used', [])
        self.console.print(f"Analysis completed using: {', '.join(analyzers)}")
        self.console.print(f"LLM enhancement: {'✅ Enabled' if enable_llm else '❌ Disabled'}")
        
        # Extract analysis_id from the comprehensive results object (passed as parent context)
        analysis_id = 'Unknown'
        if hasattr(comprehensive_results, 'analysis_id'):
            analysis_id = getattr(comprehensive_results, 'analysis_id', 'Unknown')
        elif isinstance(comprehensive_results, dict) and 'analysis_id' in comprehensive_results:
            analysis_id = comprehensive_results['analysis_id']
        else:
            # Fallback to metadata
            analysis_id = metadata.get('analysis_id', 'Unknown')
        
        self.console.print(f"Analysis ID: {analysis_id}")
        self.console.print()
    
    def _detect_version_changes(self, input_analysis) -> tuple:
        """Detect LZA version changes from the analysis"""
        
        if hasattr(input_analysis, 'stack_diffs'):
            stack_diffs = input_analysis.stack_diffs
        else:
            stack_diffs = input_analysis.get('stack_diffs', [])
        
        old_version = None
        new_version = None
        
        # First try to detect from stack description changes
        for stack in stack_diffs:
            if hasattr(stack, 'description_change'):
                desc_change = stack.description_change
            else:
                desc_change = stack.get('description_change')
            
            if desc_change and hasattr(desc_change, 'old_value') and hasattr(desc_change, 'new_value'):
                old_val = desc_change.old_value or ""
                new_val = desc_change.new_value or ""
                
                # Look for version patterns
                import re
                old_match = re.search(r'Version (\d+\.\d+\.\d+)', old_val)
                new_match = re.search(r'Version (\d+\.\d+\.\d+)', new_val)
                
                if old_match and new_match:
                    old_version = old_match.group(1)
                    new_version = new_match.group(1)
                    break
        
        # If not found in descriptions, try SSM Parameter changes
        if not (old_version and new_version):
            for stack in stack_diffs:
                resource_changes = []
                if hasattr(stack, 'resource_changes'):
                    resource_changes = stack.resource_changes
                elif hasattr(stack, 'get'):
                    resource_changes = stack.get('resource_changes', [])
                
                for resource in resource_changes:
                    logical_id = ""
                    if hasattr(resource, 'logical_id'):
                        logical_id = resource.logical_id
                    elif hasattr(resource, 'get'):
                        logical_id = resource.get('logical_id', '')
                    
                    # Look for SsmParamAcceleratorVersion parameter
                    if 'SsmParamAcceleratorVersion' in logical_id:
                        property_changes = []
                        if hasattr(resource, 'property_changes'):
                            property_changes = resource.property_changes
                        elif hasattr(resource, 'get'):
                            property_changes = resource.get('property_changes', [])
                        
                        for prop_change in property_changes:
                            property_path = ""
                            if hasattr(prop_change, 'property_path'):
                                property_path = prop_change.property_path
                            elif hasattr(prop_change, 'get'):
                                property_path = prop_change.get('property_path', '')
                            
                            if property_path == 'Value':
                                old_val = None
                                new_val = None
                                if hasattr(prop_change, 'old_value'):
                                    old_val = prop_change.old_value
                                elif hasattr(prop_change, 'get'):
                                    old_val = prop_change.get('old_value')
                                
                                if hasattr(prop_change, 'new_value'):
                                    new_val = prop_change.new_value
                                elif hasattr(prop_change, 'get'):
                                    new_val = prop_change.get('new_value')
                                
                                if old_val and new_val:
                                    old_version = str(old_val).strip()
                                    new_version = str(new_val).strip()
                                    break
                        
                        if old_version and new_version:
                            break
                
                if old_version and new_version:
                    break
        
        if old_version and new_version and old_version != new_version:
            return (old_version, new_version)
        return None
    
    def _categorize_concerns(self, findings: List[Dict]) -> Dict[str, List]:
        """Categorize findings into concern types"""
        
        categories = defaultdict(list)
        
        for finding in findings:
            risk_level = finding.get('risk_level', '').upper()
            risk_category = finding.get('risk_category', '').lower()
            change_type = finding.get('change_type', '')
            resource_type = finding.get('resource_type', '')
            title = finding.get('title', '').lower()
            
            # Only include medium+ risk findings for concerns
            if risk_level not in ['HIGH', 'CRITICAL', 'MEDIUM']:
                continue
            
            # Categorize by type
            if 'iam' in risk_category or 'iam' in resource_type.lower():
                categories['iam_changes'].append(finding)
            elif change_type == 'deletion' or 'deletion' in title:
                categories['resource_deletions'].append(finding)
            elif risk_category == 'security':
                categories['security_configs'].append(finding)
            elif risk_category in ['network', 'connectivity']:
                categories['network_changes'].append(finding)
        
        return categories
    
    def _get_high_risk_stacks(self, findings: List[Dict]) -> List[str]:
        """Get list of stacks with highest risk findings"""
        
        stack_risk_counts = defaultdict(int)
        
        for finding in findings:
            if finding.get('risk_level') in ['CRITICAL', 'HIGH']:
                stack_name = finding.get('stack_name', '')
                if stack_name:
                    # Use the full stack name instead of simplifying it
                    # This provides meaningful identification of the actual CloudFormation stacks
                    stack_risk_counts[stack_name] += 1
        
        # Sort by risk count and return top stacks
        sorted_stacks = sorted(stack_risk_counts.items(), key=lambda x: x[1], reverse=True)
        return [stack for stack, count in sorted_stacks[:5]]
    
    def _count_by_risk_level(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by risk level"""
        
        counts = defaultdict(int)
        for finding in findings:
            risk_level = finding.get('risk_level', 'UNKNOWN').upper()
            counts[risk_level] += 1
        
        return counts
    
    def _get_affected_stack_files(self, findings: List[Dict], input_analysis) -> List[str]:
        """Get list of actual diff files affected by findings"""
        
        # Get stack names from findings
        affected_stacks = set()
        for finding in findings:
            stack_name = finding.get('stack_name', '')
            if stack_name:
                affected_stacks.add(stack_name)
        
        # Get actual file names using file mapping
        stack_files = []
        for stack_name in affected_stacks:
            if self.file_mapping and stack_name in self.file_mapping:
                # Use actual file name from mapping
                file_name = self.file_mapping[stack_name]
                stack_files.append(file_name)
            else:
                # Fallback to generated file name for compatibility
                if 'AWSAccelerator-' in stack_name:
                    # Remove AWSAccelerator- prefix and simplify
                    simplified = stack_name.replace('AWSAccelerator-', '')
                    # Keep meaningful parts: StackType-Account-Region
                    parts = simplified.split('-')
                    if len(parts) >= 3:
                        # Format as: StackType-Account-Region
                        file_name = f"{parts[0]}-{parts[1]}-{parts[2]}.diff"
                    else:
                        file_name = f"{simplified}.diff"
                else:
                    file_name = f"{stack_name}.diff"
                
                stack_files.append(file_name)
        
        # Sort for consistent output
        return sorted(list(set(stack_files)))
    
    def _get_prioritized_files(self, findings: List[Dict]) -> List[tuple]:
        """Get prioritized list of files to review with reasons"""
        
        if not self.file_mapping:
            return []
        
        file_priorities = {}
        
        for finding in findings:
            stack_name = finding.get('stack_name', '')
            risk_level = finding.get('risk_level', '')
            risk_category = finding.get('risk_category', '')
            
            if stack_name and stack_name in self.file_mapping:
                file_name = self.file_mapping[stack_name]
                
                # Determine reason based on finding type
                reason = ""
                if risk_level == 'CRITICAL':
                    reason = "Critical security/compliance issue"
                elif risk_level == 'HIGH':
                    if 'iam' in risk_category.lower():
                        reason = "High-risk IAM changes"
                    elif 'security' in risk_category.lower():
                        reason = "Security configuration changes"
                    elif 'deletion' in finding.get('title', '').lower():
                        reason = "Resource deletions detected"
                    else:
                        reason = "High-risk infrastructure changes"
                elif 'iam' in risk_category.lower():
                    reason = "IAM permission changes"
                elif 'network' in risk_category.lower():
                    reason = "Network configuration changes"
                else:
                    reason = "Infrastructure changes require review"
                
                # Priority scoring: CRITICAL=100, HIGH=50, MEDIUM=25, LOW=10
                priority_score = {
                    'CRITICAL': 100,
                    'HIGH': 50, 
                    'MEDIUM': 25,
                    'LOW': 10
                }.get(risk_level, 5)
                
                if file_name not in file_priorities:
                    file_priorities[file_name] = {'score': 0, 'reason': reason}
                
                file_priorities[file_name]['score'] += priority_score
                # Use the highest priority reason for the file
                if priority_score > {
                    'CRITICAL': 100,
                    'HIGH': 50, 
                    'MEDIUM': 25,
                    'LOW': 10
                }.get(file_priorities[file_name]['reason'].split(' ')[0] if file_priorities[file_name]['reason'] else '', 5):
                    file_priorities[file_name]['reason'] = reason
        
        # Sort by priority score descending
        sorted_files = sorted(
            file_priorities.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return [(file_name, data['reason']) for file_name, data in sorted_files]