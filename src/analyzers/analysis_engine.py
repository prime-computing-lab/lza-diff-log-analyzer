"""
Comprehensive analysis engine that coordinates LLM and rule-based analysis
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from datetime import datetime

from ..models.diff_models import DiffAnalysis, ComprehensiveAnalysisResult
from ..llm.base import BaseLLMProvider, LLMProvider, LLMMessage, LLMResponse, LLMError
from ..llm.config import LLMConfigManager, ConfigLoader
from .base import RiskAnalysisEngine, RiskAssessment, RiskFinding, RiskLevel
from .security_analyzer import SecurityRiskAnalyzer
from .network_analyzer import NetworkRiskAnalyzer
from .operational_analyzer import OperationalRiskAnalyzer
from .compliance_analyzer import OperationalComplianceAnalyzer


class ComprehensiveAnalysisEngine:
    """Main engine that coordinates rule-based and LLM-powered analysis"""
    
    def __init__(self, llm_config: Optional[LLMConfigManager] = None):
        self.llm_config = llm_config or ConfigLoader.load_default_config()
        self.risk_engine = RiskAnalysisEngine()
        self.llm_provider: Optional[BaseLLMProvider] = None
        
        # Register all analyzers
        self._register_analyzers()
    
    def _register_analyzers(self):
        """Register all risk analyzers"""
        self.risk_engine.register_analyzer(SecurityRiskAnalyzer())
        self.risk_engine.register_analyzer(NetworkRiskAnalyzer())
        self.risk_engine.register_analyzer(OperationalRiskAnalyzer())
        self.risk_engine.register_analyzer(OperationalComplianceAnalyzer())
    
    async def analyze(
        self, 
        diff_analysis: DiffAnalysis, 
        enable_llm: bool = True,
        llm_provider: Optional[str] = None,
        input_dir: Optional[str] = None
    ) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive analysis combining rule-based and LLM analysis
        
        Args:
            diff_analysis: Parsed diff analysis
            enable_llm: Whether to use LLM for additional analysis
            llm_provider: Specific LLM provider to use
            input_dir: Path to input directory containing diff files (for file name mapping)
        
        Returns:
            Complete analysis results including rule-based and LLM insights
        """
        # Start with rule-based analysis
        rule_based_assessment = await self.risk_engine.analyze(diff_analysis)
        
        # Prepare metadata
        metadata = {
            "total_stacks": diff_analysis.total_stacks,
            "total_resources_changed": diff_analysis.total_resources_changed,
            "total_iam_changes": diff_analysis.total_iam_changes,
            "analyzers_used": [analyzer.name for analyzer in self.risk_engine.analyzers],
            "llm_enabled": enable_llm
        }
        
        # Initialize result object
        analysis_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add LLM analysis if enabled
        llm_analysis = None
        combined_assessment = None
        
        if enable_llm:
            try:
                llm_analysis = await self._perform_llm_analysis(
                    diff_analysis, 
                    rule_based_assessment,
                    llm_provider,
                    input_dir
                )
                
                # Combine assessments
                combined_assessment = self._combine_assessments(
                    rule_based_assessment,
                    llm_analysis
                )
            except Exception as e:
                llm_analysis = {
                    "error": str(e),
                    "fallback_used": True
                }
                combined_assessment = rule_based_assessment.dict()
        else:
            combined_assessment = rule_based_assessment.dict()
        
        # Create and return the structured result
        return ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            input_analysis=diff_analysis,
            rule_based_analysis=rule_based_assessment.dict(),
            llm_analysis=llm_analysis,
            combined_assessment=combined_assessment,
            metadata=metadata
        )
    
    async def _perform_llm_analysis(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment,
        preferred_provider: Optional[str] = None,
        input_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform LLM-powered analysis with fallback support"""
        
        # Try preferred provider first, then fallback chain
        providers_to_try = []
        if preferred_provider:
            try:
                provider_enum = LLMProvider(preferred_provider.lower())
                providers_to_try.append(self.llm_config.get_llm_config(provider_enum))
            except (ValueError, KeyError):
                pass  # Invalid provider, will use fallback chain
        
        # Add fallback chain
        providers_to_try.extend(self.llm_config.get_fallback_configs())
        
        last_error = None
        for llm_config in providers_to_try:
            try:
                return await self._analyze_with_llm(diff_analysis, rule_based_assessment, llm_config, input_dir)
            except LLMError as e:
                last_error = e
                continue
        
        # If all providers failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise LLMError("No LLM providers available", self.llm_config.default_provider)
    
    async def _analyze_with_llm(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment,
        llm_config,
        input_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform analysis with a specific LLM provider"""
        from ..llm.base import LLMProviderFactory
        
        # Use async context manager to ensure proper cleanup
        async with LLMProviderFactory.create_provider(llm_config) as provider:
            # Check if provider is available
            if not provider.is_available():
                raise LLMError(f"Provider {llm_config.provider} is not available", llm_config.provider)
            
            # Prepare analysis prompts
            prompts = self._prepare_llm_prompts(diff_analysis, rule_based_assessment, input_dir)
            
            results = {}
            for prompt_name, messages in prompts.items():
                try:
                    response = await provider.generate(messages)
                    results[prompt_name] = {
                        "content": response.content,
                        "model": response.model,
                        "provider": response.provider.value,
                        "token_usage": response.token_usage,
                        "metadata": response.metadata
                    }
                except Exception as e:
                    results[prompt_name] = {
                        "error": str(e),
                        "model": llm_config.model,
                        "provider": llm_config.provider.value
                    }
            
            return {
                "provider": llm_config.provider.value,
                "model": llm_config.model,
                "analysis_results": results,
                "summary": self._extract_llm_summary(results)
            }
    
    def _prepare_llm_prompts(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment,
        input_dir: Optional[str] = None
    ) -> Dict[str, List[LLMMessage]]:
        """Prepare prompts for different types of LLM analysis"""
        
        # Create summary of changes for LLM context
        changes_summary = self._create_changes_summary(diff_analysis, input_dir)
        risk_summary = self._create_risk_summary(rule_based_assessment)
        
        prompts = {}
        
        # 1. Overall Risk Assessment
        prompts["overall_assessment"] = [
            LLMMessage(
                role="system",
                content="""You are an expert AWS infrastructure analyst specializing in Landing Zone Accelerator (LZA) risk assessment.

Analyze the provided CloudFormation changes and risk findings to provide an overall risk assessment for this LZA upgrade.

Focus on:
- Enterprise-wide impact
- Business continuity risks
- Regulatory compliance implications
- Operational readiness
- Recommended deployment strategy

Provide a structured assessment with clear risk levels and actionable recommendations."""
            ),
            LLMMessage(
                role="user",
                content=f"""Please analyze this LZA upgrade for overall enterprise risk:

## Change Summary
{changes_summary}

## Initial Risk Assessment
{risk_summary}

Please provide:
1. Overall risk level (LOW/MEDIUM/HIGH/CRITICAL)
2. Key risks that require immediate attention
3. Recommended deployment approach
4. Specific precautions for this upgrade
5. Business impact assessment

CRITICAL CONSTRAINTS: 
1. ONLY reference files under the appropriate content category (e.g., only mention files listed under "Files with IAM Changes" when discussing IAM risks)
2. DO NOT suggest reviewing files for issues they don't contain (e.g., don't suggest CustomizationsStack files for IAM review if they're not listed under IAM changes)
3. Base ALL file recommendations on the precise "Diff Files by Content Type" categorization provided
4. If discussing IAM changes, ONLY mention files explicitly listed under "Files with IAM Changes"""
            )
        ]
        
        # 2. Network Impact Analysis (if network changes detected)
        if self._has_network_changes(diff_analysis):
            prompts["network_impact"] = [
                LLMMessage(
                    role="system",
                    content="""You are a network architecture expert specializing in AWS enterprise networking and hub-spoke designs.

Analyze the network-related changes for potential connectivity impacts, especially focusing on:
- Hub-spoke connectivity disruption
- Cross-account network access
- On-premises connectivity via Direct Connect/VPN
- Workload-to-workload communication
- DNS and service discovery impacts

Provide specific guidance for network changes in enterprise environments."""
                ),
                LLMMessage(
                    role="user",
                    content=f"""Analyze the network impact of these LZA changes:

{self._get_network_changes_summary(diff_analysis, input_dir)}

Focus on:
1. Hub-spoke connectivity risks
2. Cross-account communication impact
3. On-premises connectivity effects
4. Recommended network testing strategy
5. Rollback considerations for network changes

CRITICAL: ONLY reference files explicitly listed under "Files with Network Changes" when recommending network-related file reviews. Do not suggest files that are not in that category."""
                )
            ]
        
        # 3. Security Impact Analysis (if security changes detected)
        if self._has_security_changes(diff_analysis):
            prompts["security_impact"] = [
                LLMMessage(
                    role="system",
                    content="""You are a cybersecurity expert specializing in AWS security architecture and IAM.

Analyze the security-related changes for potential security risks, focusing on:
- IAM permission escalation risks
- Cross-account trust changes
- Encryption and key management impacts
- Compliance and audit implications
- Security monitoring disruption

Provide specific security recommendations for enterprise environments."""
                ),
                LLMMessage(
                    role="user",
                    content=f"""Analyze the security impact of these LZA changes:

{self._get_security_changes_summary(diff_analysis, input_dir)}

Focus on:
1. IAM and access control risks
2. Encryption and data protection impacts
3. Compliance implications
4. Security monitoring effects
5. Recommended security validation steps

CRITICAL: ONLY reference files explicitly listed under "Files with IAM Changes" or "Files with Security Changes" when recommending security-related file reviews. Do not suggest files that are not in those categories."""
                )
            ]
        
        # 4. Operational Readiness Assessment
        prompts["operational_readiness"] = [
            LLMMessage(
                role="system",
                content="""You are an operations expert specializing in large-scale AWS deployments and change management.

Assess the operational readiness for this LZA upgrade, considering:
- Change management processes
- Monitoring and alerting implications
- Rollback procedures
- Communication requirements
- Risk mitigation strategies

Provide practical operational guidance for enterprise deployment."""
            ),
            LLMMessage(
                role="user",
                content=f"""Assess operational readiness for this LZA upgrade:

## Changes Overview
{changes_summary}

## Risk Findings
{risk_summary}

Provide:
1. Pre-deployment checklist
2. Monitoring strategy during deployment
3. Rollback decision criteria
4. Communication plan recommendations
5. Post-deployment validation steps"""
            )
        ]
        
        return prompts
    
    def _create_changes_summary(self, diff_analysis: DiffAnalysis, input_dir: Optional[str] = None) -> str:
        """Create a concise summary of changes for LLM analysis"""
        
        # Get file mapping if input_dir is provided
        file_mapping = {}
        if input_dir:
            try:
                from pathlib import Path
                from ..parsers.file_utils import FileManager
                file_mapping = FileManager.get_diff_file_mapping(Path(input_dir))
            except Exception:
                pass  # Fallback to no file mapping
        
        summary = f"""
**Stack Summary:**
- Total stacks: {diff_analysis.total_stacks}
- Total resource changes: {diff_analysis.total_resources_changed}
- Total IAM changes: {diff_analysis.total_iam_changes}

**Key Changes by Category:**
"""
        
        # Categorize changes
        change_categories = {}
        for stack_diff in diff_analysis.stack_diffs:
            for change in stack_diff.resource_changes:
                category = change.parsed_resource_category.value
                if category not in change_categories:
                    change_categories[category] = {"add": 0, "modify": 0, "delete": 0}
                
                if change.change_type.value == "+":
                    change_categories[category]["add"] += 1
                elif change.change_type.value == "~":
                    change_categories[category]["modify"] += 1
                elif change.change_type.value == "-":
                    change_categories[category]["delete"] += 1
        
        for category, counts in change_categories.items():
            if any(counts.values()):
                summary += f"- {category}: +{counts['add']} ~{counts['modify']} -{counts['delete']}\n"
        
        # Add critical stacks information
        if diff_analysis.stacks_with_security_changes:
            summary += f"\n**Security-sensitive stacks:** {len(diff_analysis.stacks_with_security_changes)}\n"
        
        if diff_analysis.stacks_with_deletions:
            summary += f"**Stacks with deletions:** {len(diff_analysis.stacks_with_deletions)}\n"
        
        # Add PRECISE file-to-content mapping for user reference
        if file_mapping:
            summary += f"\n**Diff Files by Content Type:**\n"
            
            # Create precise categorization
            iam_files = []
            security_files = []
            network_files = []
            deletion_files = []
            version_only_files = []
            
            for stack_diff in diff_analysis.stack_diffs:
                stack_name = stack_diff.stack_name
                file_name = file_mapping.get(stack_name, f"{stack_name}.diff")
                
                # PRECISE categorization based on actual content
                has_iam = len(stack_diff.iam_statement_changes) > 0
                has_deletions = stack_diff.has_deletions
                has_security = stack_diff.has_security_changes
                has_network = any('network' in change.parsed_resource_category.value.lower() or 
                                 any(net_type in change.resource_type for net_type in ["VPC", "TransitGateway", "Route", "SecurityGroup"])
                                 for change in stack_diff.resource_changes)
                
                # Only mention files under categories they actually belong to
                if has_iam:
                    iam_count = len(stack_diff.iam_statement_changes)
                    iam_files.append(f"  • {file_name} ({iam_count} IAM changes)")
                
                if has_deletions:
                    deletion_files.append(f"  • {file_name} (Resource deletions)")
                
                if has_security and not has_iam:  # Avoid double-counting IAM as security
                    security_files.append(f"  • {file_name} (Security config changes)")
                
                if has_network:
                    network_files.append(f"  • {file_name} (Network changes)")
                
                if not (has_iam or has_deletions or has_security or has_network):
                    version_only_files.append(f"  • {file_name} (Version/parameter updates only)")
            
            # Show precise categories
            if iam_files:
                summary += f"\n**Files with IAM Changes ({len(iam_files)} files):**\n"
                for file_info in iam_files[:10]:  # Show up to 10
                    summary += f"{file_info}\n"
                if len(iam_files) > 10:
                    summary += f"  ... and {len(iam_files) - 10} more IAM files\n"
            
            if deletion_files:
                summary += f"\n**Files with Resource Deletions ({len(deletion_files)} files):**\n"
                for file_info in deletion_files[:5]:
                    summary += f"{file_info}\n"
            
            if security_files:
                summary += f"\n**Files with Security Changes ({len(security_files)} files):**\n"
                for file_info in security_files[:5]:
                    summary += f"{file_info}\n"
            
            if network_files:
                summary += f"\n**Files with Network Changes ({len(network_files)} files):**\n"
                for file_info in network_files[:5]:
                    summary += f"{file_info}\n"
            
            if version_only_files:
                summary += f"\n**Files with Version Updates Only ({len(version_only_files)} files):**\n"
                for file_info in version_only_files[:3]:
                    summary += f"{file_info}\n"
                if len(version_only_files) > 3:
                    summary += f"  ... and {len(version_only_files) - 3} more version-only files\n"
        
        return summary
    
    def _create_risk_summary(self, assessment: RiskAssessment) -> str:
        """Create a summary of risk findings"""
        summary = f"""
**Risk Assessment Summary:**
- Overall Risk Level: {assessment.overall_risk_level.value}
- Total Findings: {assessment.total_findings}
- Critical: {assessment.critical_count}, High: {assessment.high_count}, Medium: {assessment.medium_count}, Low: {assessment.low_count}

**Risk Categories:**
- Security: {assessment.security_risks}
- Connectivity: {assessment.connectivity_risks}
- Operational: {assessment.operational_risks}
- Compliance: {assessment.compliance_risks}
- Data Loss: {assessment.data_loss_risks}

**Recommendation:** {assessment.recommended_action}
"""
        
        # Add critical findings details
        critical_findings = assessment.get_critical_findings()
        if critical_findings:
            summary += "\n**Critical Findings:**\n"
            for finding in critical_findings[:3]:  # Limit to top 3
                summary += f"- {finding.title}: {finding.impact_description}\n"
        
        return summary
    
    def _has_network_changes(self, diff_analysis: DiffAnalysis) -> bool:
        """Check if there are network-related changes"""
        network_types = {
            "AWS::EC2::VPC", "AWS::EC2::Subnet", "AWS::EC2::RouteTable",
            "AWS::EC2::TransitGateway", "AWS::EC2::SecurityGroup",
            "AWS::DirectConnect::VirtualInterface", "AWS::EC2::VPNConnection"
        }
        
        for stack_diff in diff_analysis.stack_diffs:
            for change in stack_diff.resource_changes:
                if change.resource_type in network_types:
                    return True
        return False
    
    def _has_security_changes(self, diff_analysis: DiffAnalysis) -> bool:
        """Check if there are security-related changes"""
        return diff_analysis.total_iam_changes > 0 or any(
            stack_diff.has_security_changes
            for stack_diff in diff_analysis.stack_diffs
        )
    
    def _get_network_changes_summary(self, diff_analysis: DiffAnalysis, input_dir: Optional[str] = None) -> str:
        """Get summary of network changes"""
        # Get file mapping for referencing specific files
        file_mapping = {}
        if input_dir:
            try:
                from pathlib import Path
                from ..parsers.file_utils import FileManager
                file_mapping = FileManager.get_diff_file_mapping(Path(input_dir))
            except Exception:
                pass
        
        network_changes = []
        for stack_diff in diff_analysis.stack_diffs:
            stack_has_network_changes = False
            for change in stack_diff.resource_changes:
                if "network" in change.parsed_resource_category.value.lower() or \
                   any(net_type in change.resource_type for net_type in ["VPC", "TransitGateway", "Route", "SecurityGroup"]):
                    if not stack_has_network_changes:
                        # Add file reference for this stack
                        file_name = file_mapping.get(stack_diff.stack_name, f"{stack_diff.stack_name}.diff")
                        network_changes.append(f"\n📄 **{file_name}** ({stack_diff.stack_name}):")
                        stack_has_network_changes = True
                    network_changes.append(f"  - {change.resource_type} '{change.logical_id}' ({change.change_type.value})")
        
        return "\n".join(network_changes[:25])  # Increased limit to accommodate file grouping
    
    def _get_security_changes_summary(self, diff_analysis: DiffAnalysis, input_dir: Optional[str] = None) -> str:
        """Get summary of security changes"""
        # Get file mapping for referencing specific files
        file_mapping = {}
        if input_dir:
            try:
                from pathlib import Path
                from ..parsers.file_utils import FileManager
                file_mapping = FileManager.get_diff_file_mapping(Path(input_dir))
            except Exception:
                pass
        
        security_changes = []
        stacks_with_security = set()
        
        for stack_diff in diff_analysis.stack_diffs:
            stack_has_security_changes = False
            for change in stack_diff.resource_changes:
                if "security" in change.parsed_resource_category.value.lower() or \
                   "iam" in change.parsed_resource_category.value.lower():
                    if not stack_has_security_changes:
                        # Add file reference for this stack
                        file_name = file_mapping.get(stack_diff.stack_name, f"{stack_diff.stack_name}.diff")
                        security_changes.append(f"\n📄 **{file_name}** ({stack_diff.stack_name}):")
                        stack_has_security_changes = True
                        stacks_with_security.add(stack_diff.stack_name)
                    security_changes.append(f"  - {change.resource_type} '{change.logical_id}' ({change.change_type.value})")
            
            # Add IAM changes for this stack
            if len(stack_diff.iam_statement_changes) > 0:
                if not stack_has_security_changes:
                    file_name = file_mapping.get(stack_diff.stack_name, f"{stack_diff.stack_name}.diff")
                    security_changes.append(f"\n📄 **{file_name}** ({stack_diff.stack_name}):")
                    stacks_with_security.add(stack_diff.stack_name)
                security_changes.append(f"  - {len(stack_diff.iam_statement_changes)} IAM statement changes")
        
        return "\n".join(security_changes[:25])  # Increased limit to accommodate file grouping
    
    def _extract_llm_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Extract key insights from LLM analysis results"""
        summary = {}
        
        for analysis_type, result in results.items():
            if "error" not in result:
                # Extract first few lines as summary
                content = result.get("content", "")
                lines = content.split("\n")
                summary[analysis_type] = "\n".join(lines[:5])  # First 5 lines
            else:
                summary[analysis_type] = f"Analysis failed: {result['error']}"
        
        return summary
    
    def _combine_assessments(
        self,
        rule_based: RiskAssessment,
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine rule-based and LLM analysis into final assessment"""
        
        # Start with rule-based assessment
        combined = rule_based.dict()
        
        # Add LLM insights
        combined["llm_insights"] = llm_analysis.get("summary", {})
        combined["enhanced_recommendations"] = []
        
        # Extract recommendations from LLM analysis
        for analysis_type, result in llm_analysis.get("analysis_results", {}).items():
            if "error" not in result:
                content = result.get("content", "")
                # Simple extraction of recommendations (could be enhanced with better parsing)
                if "recommend" in content.lower():
                    lines = content.split("\n")
                    rec_lines = [line for line in lines if "recommend" in line.lower()]
                    combined["enhanced_recommendations"].extend(rec_lines[:3])
        
        # Enhance overall assessment
        if "overall_assessment" in llm_analysis.get("analysis_results", {}):
            overall_content = llm_analysis["analysis_results"]["overall_assessment"].get("content", "")
            if "CRITICAL" in overall_content.upper():
                combined["llm_risk_level"] = "CRITICAL"
            elif "HIGH" in overall_content.upper():
                combined["llm_risk_level"] = "HIGH"
            elif "MEDIUM" in overall_content.upper():
                combined["llm_risk_level"] = "MEDIUM"
            else:
                combined["llm_risk_level"] = "LOW"
        
        return combined
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Get information about analysis capabilities"""
        return {
            "rule_based_analyzers": self.risk_engine.get_analyzer_info(),
            "llm_providers": {
                provider.value: {
                    "enabled": config.enabled,
                    "model": config.model
                }
                for provider, config in self.llm_config.providers.items()
            },
            "supported_analysis_types": [
                "overall_assessment",
                "network_impact",
                "security_impact", 
                "operational_readiness"
            ]
        }
    
    async def _run_single_llm_analysis(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment,
        analysis_type: str,
        preferred_provider: Optional[str] = None
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """
        Run a single LLM analysis step, returning either streaming or non-streaming result
        
        Args:
            diff_analysis: The diff analysis data
            rule_based_assessment: Rule-based assessment results
            analysis_type: Type of analysis to perform
            preferred_provider: Preferred LLM provider
            
        Returns:
            Either a streaming response (AsyncIterator) or complete result (Dict)
        """
        # Get LLM provider configuration
        providers_to_try = []
        if preferred_provider:
            try:
                provider_enum = LLMProvider(preferred_provider.lower())
                providers_to_try.append(self.llm_config.get_llm_config(provider_enum))
            except (ValueError, KeyError):
                pass
        
        providers_to_try.extend(self.llm_config.get_fallback_configs())
        
        # Prepare the prompt for this analysis type
        prompts = self._prepare_llm_prompts(diff_analysis, rule_based_assessment)
        
        if analysis_type not in prompts:
            raise LLMError(f"Unknown analysis type: {analysis_type}", LLMProvider.OLLAMA)
        
        messages = prompts[analysis_type]
        
        # Try providers in order
        last_error = None
        for llm_config in providers_to_try:
            try:
                from ..llm.base import LLMProviderFactory
                provider = LLMProviderFactory.create_provider(llm_config)
                
                if not provider.is_available():
                    continue
                
                # Try streaming first if supported
                if hasattr(provider, 'stream_generate'):
                    try:
                        return provider.stream_generate(messages)
                    except Exception:
                        # Fall back to non-streaming
                        pass
                
                # Non-streaming fallback
                response = await provider.generate(messages)
                return {
                    "content": response.content,
                    "model": response.model,
                    "provider": response.provider.value,
                    "token_usage": response.token_usage,
                    "metadata": response.metadata
                }
                
            except Exception as e:
                last_error = e
                continue
        
        # If all providers failed
        if last_error:
            raise last_error
        else:
            raise LLMError("No LLM providers available", LLMProvider.OLLAMA)
    
    def _create_non_llm_result(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment
    ) -> ComprehensiveAnalysisResult:
        """Create a comprehensive result without LLM analysis"""
        analysis_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            "total_stacks": diff_analysis.total_stacks,
            "total_resources_changed": diff_analysis.total_resources_changed,
            "total_iam_changes": diff_analysis.total_iam_changes,
            "analyzers_used": [analyzer.name for analyzer in self.risk_engine.analyzers],
            "llm_enabled": False
        }
        
        return ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            input_analysis=diff_analysis,
            rule_based_analysis=rule_based_assessment.dict(),
            llm_analysis=None,
            combined_assessment=rule_based_assessment.dict(),
            metadata=metadata
        )
    
    def _create_comprehensive_result(
        self,
        diff_analysis: DiffAnalysis,
        rule_based_assessment: RiskAssessment,
        llm_results: Dict[str, Any],
        llm_provider: Optional[str] = None
    ) -> ComprehensiveAnalysisResult:
        """Create a comprehensive result with LLM analysis"""
        analysis_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            "total_stacks": diff_analysis.total_stacks,
            "total_resources_changed": diff_analysis.total_resources_changed,
            "total_iam_changes": diff_analysis.total_iam_changes,
            "analyzers_used": [analyzer.name for analyzer in self.risk_engine.analyzers],
            "llm_enabled": True
        }
        
        # Structure LLM analysis
        llm_analysis = {
            "provider": llm_provider or "unknown",
            "model": "unknown",
            "analysis_results": llm_results,
            "summary": self._extract_llm_summary(llm_results)
        }
        
        # Extract provider/model info from first successful result
        for result in llm_results.values():
            if isinstance(result, dict) and "provider" in result:
                llm_analysis["provider"] = result["provider"]
                llm_analysis["model"] = result.get("model", "unknown")
                break
        
        # Combine assessments
        combined_assessment = self._combine_assessments(rule_based_assessment, llm_analysis)
        
        return ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            input_analysis=diff_analysis,
            rule_based_analysis=rule_based_assessment.dict(),
            llm_analysis=llm_analysis,
            combined_assessment=combined_assessment,
            metadata=metadata
        )