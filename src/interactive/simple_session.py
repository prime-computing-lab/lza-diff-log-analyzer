"""
Simplified interactive session with reliable terminal input/output
"""

import asyncio
import sys
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ..models.diff_models import ComprehensiveAnalysisResult
from ..llm.config import ConfigLoader
from ..llm.base import LLMProviderFactory, LLMMessage


class SimpleInteractiveSession:
    """Simplified interactive session focused on reliable input/output"""
    
    def __init__(self, console: Console):
        self.console = console
        self.llm_config = ConfigLoader.load_default_config()
        self.llm_provider = None
        self.analysis_data = None
        self.context = {}
        self.input_dir = None
        self.file_mapping = {}
        
    async def start(self, input_dir: str, analysis_results: Optional[ComprehensiveAnalysisResult] = None):
        """Start the interactive session with simplified flow"""
        self.analysis_data = analysis_results
        self.input_dir = input_dir
        
        # Show welcome message
        self._show_welcome()
        
        # Initialize LLM if possible
        await self._init_llm()
        
        # Create analysis context with file mapping
        self._prepare_context()
        
        # Start simple Q&A loop
        await self._simple_qa_loop()
    
    def _show_welcome(self):
        """Show simple welcome message"""
        welcome = """
🤖 **LZA Analysis Assistant**

I can help you understand your CloudFormation changes and assess risks.

**Example questions:**
• "What are the biggest risks in this upgrade?"
• "Are the IAM changes safe?"
• "Which stacks should I review first?"
• "How do I test these changes?"

**Commands:** `help`, `summary`, `exit`
        """
        
        panel = Panel(Markdown(welcome), title="AI Assistant", border_style="blue")
        self.console.print(panel)
        self.console.print()
    
    async def _init_llm(self):
        """Simple LLM initialization"""
        try:
            default_config = self.llm_config.get_default_config()
            self.llm_provider = LLMProviderFactory.create_provider(default_config)
            
            if self.llm_provider and self.llm_provider.is_available():
                self.console.print(f"✅ AI powered by {default_config.model}")
            else:
                # Try to get specific error details
                error_message = "ℹ️ Using rule-based responses (LLM unavailable)"
                if hasattr(self.llm_provider, 'get_availability_error'):
                    availability_error = self.llm_provider.get_availability_error()
                    if availability_error:
                        error_message = f"❌ LLM unavailable: {availability_error}"
                
                self.console.print(error_message)
                self.llm_provider = None
        except Exception:
            self.console.print("ℹ️ Using rule-based responses (LLM unavailable)")
            self.llm_provider = None
    
    def _prepare_context(self):
        """Prepare analysis context for responses"""
        if not self.analysis_data:
            self.context = {"status": "no_data"}
            return
        
        # Get file mapping for actual diff file references
        try:
            if self.input_dir:
                from pathlib import Path
                from ..parsers.file_utils import FileManager
                self.file_mapping = FileManager.get_diff_file_mapping(Path(self.input_dir))
        except Exception:
            self.file_mapping = {}
            
        try:
            # Extract key information for context
            if hasattr(self.analysis_data, 'get_enhanced_context_for_llm'):
                # Proper ComprehensiveAnalysisResult object
                self.context = self.analysis_data.get_enhanced_context_for_llm()
            elif isinstance(self.analysis_data, dict):
                # Fallback for raw dict data (legacy compatibility)
                self.context = self._extract_context_from_dict(self.analysis_data)
            else:
                self.context = {"status": "basic"}
                
            # Add file mapping to context
            self.context["file_mapping"] = self.file_mapping
            self.context["input_dir"] = self.input_dir
        except Exception as e:
            # Enhanced error handling with debug info
            print(f"Warning: Context preparation failed: {e}")
            self.context = {
                "status": "error", 
                "file_mapping": self.file_mapping,
                "error_details": str(e)
            }
    
    def _extract_context_from_dict(self, data: dict) -> dict:
        """
        Extract context from raw dict data (fallback for legacy compatibility)
        
        Args:
            data: Raw analysis data dictionary
            
        Returns:
            Context dictionary for AI assistant
        """
        try:
            # Extract basic statistics
            input_analysis = data.get('input_analysis', {})
            rule_analysis = data.get('rule_based_analysis', {})
            
            # Build basic context structure
            context = {
                "overview": {
                    "total_stacks": input_analysis.get('total_stacks', 0),
                    "total_resources_changed": input_analysis.get('total_resources_changed', 0),
                    "total_iam_changes": input_analysis.get('total_iam_changes', 0),
                    "analysis_timestamp": input_analysis.get('analysis_timestamp')
                },
                "risk_assessment": {
                    "overall_risk_level": rule_analysis.get('overall_risk_level'),
                    "total_findings": rule_analysis.get('total_findings', 0),
                    "critical_count": rule_analysis.get('critical_count', 0),
                    "high_count": rule_analysis.get('high_count', 0),
                    "medium_count": rule_analysis.get('medium_count', 0),
                    "low_count": rule_analysis.get('low_count', 0)
                },
                "analysis_metadata": {
                    "analysis_id": data.get('analysis_id'),
                    "created_at": data.get('created_at'),
                    "analyzers_used": data.get('metadata', {}).get('analyzers_used', []),
                    "llm_enabled": data.get('metadata', {}).get('llm_enabled', False)
                }
            }
            
            # Extract stack information
            stack_diffs = input_analysis.get('stack_diffs', [])
            stacks = {}
            iam_changes = []
            high_risk_changes = []
            
            for stack in stack_diffs:
                stack_name = stack.get('stack_name', '')
                stack_info = {
                    "account_id": stack.get('account_id'),
                    "region": stack.get('region'),
                    "resource_changes_count": len(stack.get('resource_changes', [])),
                    "iam_changes_count": len(stack.get('iam_statement_changes', [])),
                    "has_deletions": stack.get('has_deletions', False),
                    "has_security_changes": stack.get('has_security_changes', False)
                }
                stacks[stack_name] = stack_info
                
                # Extract IAM changes
                for iam in stack.get('iam_statement_changes', []):
                    iam_changes.append({
                        "stack": stack_name,
                        "effect": iam.get('effect'),
                        "action": iam.get('action'),
                        "resource": iam.get('resource'),
                        "principal": iam.get('principal'),
                        "change_type": iam.get('change_type')
                    })
                
                # Extract high-risk changes
                for rc in stack.get('resource_changes', []):
                    if rc.get('change_type') == '-':  # Deletions
                        high_risk_changes.append({
                            "stack": stack_name,
                            "resource": rc.get('logical_id'),
                            "type": rc.get('resource_type'),
                            "change": rc.get('change_type'),
                            "reason": "Deletion"
                        })
            
            context.update({
                "stacks": stacks,
                "iam_changes": iam_changes,
                "high_risk_changes": high_risk_changes
            })
            
            return context
            
        except Exception as e:
            print(f"Warning: Failed to extract context from dict: {e}")
            return {
                "status": "extraction_failed",
                "error": str(e),
                "overview": {"total_stacks": 0, "total_resources_changed": 0, "total_iam_changes": 0}
            }
    
    async def _simple_qa_loop(self):
        """Simple, reliable Q&A loop"""
        while True:
            try:
                # Clear any output buffers
                sys.stdout.flush()
                sys.stderr.flush()
                
                # Simple prompt - no Rich components that interfere with input
                self.console.print("\n" + "=" * 60)
                self.console.print("💬 Ask a question (or 'exit' to quit):")
                
                # Use plain input() for reliable terminal interaction
                question = input("> ").strip()
                
                # Show what user typed for clarity
                self.console.print(f"❓ You asked: [cyan]{question}[/cyan]")
                self.console.print()
                
                if not question:
                    continue
                    
                # Handle exit commands
                if question.lower() in ['exit', 'quit', 'q']:
                    self.console.print("👋 Goodbye!")
                    break
                
                # Handle special commands
                if question.lower() == 'help':
                    self._show_help()
                    continue
                elif question.lower() == 'summary':
                    self._show_summary()
                    continue
                
                # Process the question
                await self._answer_question(question)
                
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n👋 Session ended")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    async def _answer_question(self, question: str):
        """Answer a question using LLM or rule-based fallback"""
        self.console.print("🤔 Thinking...")
        
        # Try LLM first
        if self.llm_provider:
            try:
                answer = await self._get_llm_answer(question)
                if answer:
                    self._display_answer(answer, "AI Assistant")
                    return
            except Exception as e:
                # Enhanced error reporting for AI failures
                if "ollama" in str(e).lower():
                    self.console.print(f"[yellow]AI error: {e}[/yellow]")
                    self.console.print("[dim]💡 Tip: Check 'ollama serve' is running and model is available[/dim]")
                else:
                    self.console.print(f"[yellow]AI error: {e}[/yellow]")
        
        # Fallback to rule-based
        answer = self._get_rule_based_answer(question)
        self._display_answer(answer, "Rule-based Assistant")
    
    async def _get_llm_answer(self, question: str) -> Optional[str]:
        """Get answer from LLM with simplified context"""
        if not self.llm_provider:
            return None
        
        # Create simple context summary
        context_summary = self._create_simple_context(question)
        
        # Create messages
        messages = [
            LLMMessage(
                role="system",
                content="""You are an AWS Landing Zone Accelerator (LZA) expert analyzing CloudFormation diff logs from an LZA upgrade.

IMPORTANT: Your responses must ONLY be based on the specific diff log files that were analyzed. Do NOT provide generic AWS logging advice.

When recommending which files to review, ALWAYS reference the actual diff file names provided in the analysis data. Users need to know exactly which files to examine.

The analysis covers CloudFormation stack differences showing resource changes, IAM modifications, and parameter updates from the LZA upgrade. Focus your responses on:
- Specific stack names and their corresponding diff file names
- Actual resource changes found in the diffs
- IAM changes identified in the stack comparisons
- Risk findings from the automated analysis

CRITICAL CONSTRAINTS:
1. ONLY reference files under the appropriate content category (e.g., only mention files listed under "Files with IAM Changes" when discussing IAM risks)
2. DO NOT suggest reviewing files for issues they don't contain (e.g., never suggest CustomizationsStack files for IAM review if they're not listed under IAM changes)
3. Base ALL file recommendations on the precise file categorization provided in the analysis data
4. If discussing IAM changes, ONLY mention files explicitly listed under "Files with IAM Changes"
5. Never make assumptions about file contents - only reference what is explicitly categorized

Provide clear, actionable advice based ONLY on the provided analysis data and precise file categorizations."""
            ),
            LLMMessage(
                role="user", 
                content=f"""Analysis Data: {context_summary}

Question: {question}

Please provide a helpful answer based on the analysis data."""
            )
        ]
        
        response = await self.llm_provider.generate(messages)
        return response.content
    
    def _create_simple_context(self, question: str) -> str:
        """Create simplified context summary focused on diff files"""
        if self.context.get("status") in ["no_data", "error", "basic"]:
            return "Limited analysis data available"
        
        # Extract key metrics
        overview = self.context.get("overview", {})
        risk_assessment = self.context.get("risk_assessment", {})
        
        context_text = f"""
LZA CloudFormation Diff Analysis Results:
- Total stack diff files analyzed: {overview.get('total_stacks', 0)}
- Resource changes found in diffs: {overview.get('total_resources_changed', 0)}
- IAM changes found in stack diffs: {overview.get('total_iam_changes', 0)}
- Overall risk level: {risk_assessment.get('overall_risk_level', 'Unknown')}
- Total findings from diff analysis: {risk_assessment.get('total_findings', 0)}

Diff Files Available for Review:
"""
        
        # Add PRECISE file categorization by content type
        if self.file_mapping and self.analysis_data:
            context_text += "Diff files categorized by actual content:\n"
            
            # Get actual stack diff data to categorize files precisely
            stack_diffs = getattr(self.analysis_data, 'input_analysis', {})
            if hasattr(stack_diffs, 'stack_diffs'):
                stack_diffs = stack_diffs.stack_diffs
            elif isinstance(stack_diffs, dict):
                stack_diffs = stack_diffs.get('stack_diffs', [])
            else:
                stack_diffs = []
            
            iam_files = []
            deletion_files = []
            version_only_files = []
            
            for stack_diff in stack_diffs:
                try:
                    # Handle both Pydantic objects and dictionaries
                    if hasattr(stack_diff, 'stack_name'):
                        # Pydantic object (StackDiff model)
                        stack_name = stack_diff.stack_name
                        iam_changes = getattr(stack_diff, 'iam_statement_changes', [])
                        has_deletions = getattr(stack_diff, 'has_deletions', False)
                    elif isinstance(stack_diff, dict):
                        # Dictionary object  
                        stack_name = stack_diff.get('stack_name', '')
                        iam_changes = stack_diff.get('iam_statement_changes', [])
                        has_deletions = stack_diff.get('has_deletions', False)
                    else:
                        # Fallback for unknown type
                        stack_name = str(stack_diff) if stack_diff else ''
                        iam_changes = []
                        has_deletions = False
                except Exception:
                    # Graceful fallback if any attribute access fails
                    stack_name = ''
                    iam_changes = []
                    has_deletions = False
                
                if stack_name in self.file_mapping:
                    file_name = self.file_mapping[stack_name]
                    
                    if len(iam_changes) > 0:
                        iam_files.append(f"- {file_name} ({len(iam_changes)} IAM changes)")
                    elif has_deletions:
                        deletion_files.append(f"- {file_name} (Resource deletions)")
                    else:
                        version_only_files.append(f"- {file_name} (Version updates only)")
            
            if iam_files:
                context_text += f"\nFiles with IAM Changes ({len(iam_files)} files):\n"
                for file_info in iam_files[:5]:
                    context_text += f"{file_info}\n"
            
            if deletion_files:
                context_text += f"\nFiles with Resource Deletions ({len(deletion_files)} files):\n"
                for file_info in deletion_files[:3]:
                    context_text += f"{file_info}\n"
            
            if version_only_files:
                context_text += f"\nFiles with Version Updates Only ({len(version_only_files)} files):\n"
                for file_info in version_only_files[:3]:
                    context_text += f"{file_info}\n"
                if len(version_only_files) > 3:
                    context_text += f"... and {len(version_only_files) - 3} more version-only files\n"
        else:
            context_text += "Note: Detailed file categorization not available\n"
        
        # Add stack-specific information
        if 'stack' in question.lower() or 'file' in question.lower():
            context_text += "\nThis analysis covers CloudFormation stack diff files showing changes between LZA versions."
        
        # Add relevant details based on question type
        question_lower = question.lower()
        if 'iam' in question_lower or 'permission' in question_lower:
            iam_changes = self.context.get("iam_changes", [])
            if iam_changes:
                context_text += f"\nIAM changes identified in stack diffs: {len(iam_changes)} modifications"
        
        if 'risk' in question_lower or 'concern' in question_lower or 'high' in question_lower:
            findings = risk_assessment.get('findings', [])
            critical_findings = [f for f in findings if f.get('risk_level') == 'CRITICAL']
            high_findings = [f for f in findings if f.get('risk_level') == 'HIGH']
            
            if critical_findings or high_findings:
                context_text += f"\nHigh-risk findings: {len(critical_findings)} critical, {len(high_findings)} high priority"
                
                # Include specific stack names and file names for high-risk findings
                high_risk_stacks = set()
                high_risk_files = []
                for finding in (critical_findings + high_findings)[:5]:  # Top 5
                    if 'stack_name' in finding:
                        stack_name = finding['stack_name']
                        high_risk_stacks.add(stack_name)
                        # Add corresponding file name if available
                        if self.file_mapping and stack_name in self.file_mapping:
                            file_name = self.file_mapping[stack_name]
                            high_risk_files.append(f"{file_name} ({stack_name})")
                
                if high_risk_files:
                    context_text += f"\nHigh-risk diff files to prioritize:\n"
                    for file_info in high_risk_files[:3]:
                        context_text += f"- {file_info}\n"
                    if len(high_risk_files) > 3:
                        context_text += f"... and {len(high_risk_files)-3} more high-risk files"
                elif high_risk_stacks:
                    context_text += f"\nStacks with high-risk changes: {', '.join(list(high_risk_stacks)[:3])}"
                    if len(high_risk_stacks) > 3:
                        context_text += f" and {len(high_risk_stacks)-3} others"
        
        return context_text.strip()
    
    def _get_rule_based_answer(self, question: str) -> str:
        """Simple rule-based responses"""
        question_lower = question.lower()
        
        if 'iam' in question_lower or 'permission' in question_lower:
            return self._get_iam_answer()
        elif 'risk' in question_lower or 'concern' in question_lower:
            return self._get_risk_answer()
        elif 'test' in question_lower or 'deploy' in question_lower:
            return self._get_deployment_answer()
        elif 'stack' in question_lower or 'file' in question_lower:
            return self._get_stack_answer()
        else:
            return self._get_general_answer()
    
    def _get_iam_answer(self) -> str:
        """IAM-focused answer"""
        base_answer = """
**IAM Changes in LZA Upgrades**

Most IAM changes in LZA upgrades are routine maintenance:
• Cross-account role updates for Log Archive/Audit accounts
• Service role permission adjustments for new LZA features
• Control Tower integration updates

**Review checklist:**
1. Check for wildcard permissions (*:*)
2. Verify cross-account trust relationships
3. Ensure Log Archive account access is maintained
4. Test security service functionality

**Testing:** Deploy to non-production first and verify cross-account logging works.
        """
        
        # Add specific data if available
        if self.context.get("status") not in ["no_data", "error", "basic"]:
            iam_changes = self.context.get("iam_changes", [])
            if iam_changes:
                base_answer += f"\n**In your analysis:** {len(iam_changes)} IAM changes detected"
        
        return base_answer.strip()
    
    def _get_risk_answer(self) -> str:
        """Risk-focused answer"""
        base_answer = """
**LZA Risk Assessment**

**Normal upgrade patterns:**
• 200-500 findings (typical for major upgrades)
• 70% IAM adjustments (expected)
• SSM parameter updates (routine)

**Focus on:**
🔴 Resource deletions
🔴 Security service changes  
🔴 Network connectivity modifications
🟡 New IAM permissions
🟢 Parameter updates

**Key question:** Can workloads continue operating normally?
        """
        
        # Add specific risk data if available
        if self.context.get("status") not in ["no_data", "error", "basic"]:
            risk_assessment = self.context.get("risk_assessment", {})
            if risk_assessment:
                risk_level = risk_assessment.get("overall_risk_level", "Unknown")
                total_findings = risk_assessment.get("total_findings", 0)
                base_answer += f"\n**Your analysis:** {risk_level} risk, {total_findings} findings"
        
        return base_answer.strip()
    
    def _get_deployment_answer(self) -> str:
        """Deployment guidance"""
        return """
**Safe LZA Deployment Process**

**Pre-deployment:**
1. Test in non-production environment
2. Verify admin access to all accounts
3. Document rollback procedure
4. Schedule maintenance window

**Testing checklist:**
□ LZA pipeline runs successfully
□ Cross-account access works
□ Centralized logging functional
□ Security services operational

**Deployment:**
• Have support team available
• Monitor for 24-48 hours
• Validate key applications

**Rollback if:** Pipeline failures, access issues, service disruptions
        """
    
    def _get_stack_answer(self) -> str:
        """Stack-focused answer"""
        base_answer = """
**LZA Stack Prioritization**

**High-priority stacks:**
1. **DependenciesStack** - Core IAM and cross-account setup
2. **SecurityStack** - Central security services
3. **NetworkStack** - VPC and connectivity
4. **LoggingStack** - Centralized logging

**Review approach:**
• Dependencies: Check cross-account IAM changes
• Security: Verify service configurations
• Network: Ensure connectivity maintained
• Account-specific: Lower priority unless deletions
        """
        
        # Add specific stack data if available
        if self.context.get("status") not in ["no_data", "error", "basic"]:
            stacks = self.context.get("stacks", {})
            if stacks:
                base_answer += f"\n**Your analysis:** {len(stacks)} stacks with changes"
                
                # Find high-risk stacks
                risky_stacks = []
                for stack_name, stack_data in stacks.items():
                    if (stack_data.get("has_deletions") or 
                        stack_data.get("iam_changes_count", 0) > 10):
                        risky_stacks.append(stack_name)
                
                if risky_stacks:
                    base_answer += f"\n**Priority review:** {', '.join(risky_stacks[:3])}"
        
        return base_answer.strip()
    
    def _get_general_answer(self) -> str:
        """General guidance"""
        return """
**LZA Upgrade Guidance**

LZA upgrades are generally safe but require validation:

**What's happening:** Version 1.10.0 → 1.12.1 upgrade with infrastructure updates

**Typical changes:**
• IAM role/policy updates (most findings)
• SSM parameter versions
• Service configurations
• New feature enablement

**Key principles:**
1. Test in non-production first
2. Focus on IAM, security, network changes
3. Verify business-critical services
4. Have rollback plan ready

**Ask specific questions about:**
• Individual stacks or files
• Risk assessment details
• Testing procedures
• Deployment planning
        """
    
    def _display_answer(self, answer: str, source: str):
        """Display answer in a simple, clean format"""
        panel = Panel(
            Markdown(answer.strip()),
            title=f"💬 {source}",
            border_style="green"
        )
        self.console.print(panel)
        self.console.print()
    
    def _show_help(self):
        """Show help information"""
        help_text = """
**Commands:**
• `help` - Show this help
• `summary` - Analysis overview
• `exit` - End session

**Example questions:**
• "What are the biggest risks?"
• "Are IAM changes safe?"
• "Which stacks need review?"
• "How do I test this safely?"
• "What's the deployment process?"
        """
        self._display_answer(help_text, "Help")
    
    def _show_summary(self):
        """Show analysis summary"""
        if self.context.get("status") in ["no_data", "error", "basic"]:
            summary = "Analysis data not available. Limited guidance only."
        else:
            overview = self.context.get("overview", {})
            risk_assessment = self.context.get("risk_assessment", {})
            
            summary = f"""
**Analysis Summary:**
• Stacks analyzed: {overview.get('total_stacks', 0)}
• Resource changes: {overview.get('total_resources_changed', 0)}
• IAM changes: {overview.get('total_iam_changes', 0)}
• Risk level: {risk_assessment.get('overall_risk_level', 'Unknown')}
• Total findings: {risk_assessment.get('total_findings', 0)}

**Recommendation:** {risk_assessment.get('recommendation', 'Review changes carefully')}
            """
        
        self._display_answer(summary, "Summary")