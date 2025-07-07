#!/usr/bin/env python3
"""
Simplified LZA Diff Analyzer CLI - Clean, maintainable implementation
"""

import click
import asyncio
from pathlib import Path
from rich.console import Console

from .analysis_runner import AnalysisRunner, ReportGenerator
from ..models.diff_models import DiffAnalysis

console = Console()


@click.command()
@click.version_option(version="0.1.0")
@click.option(
    "--input-dir", "-i",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing diff log files"
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default="./output",
    help="Output directory for analysis results"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "yaml", "html"]),
    default="json",
    help="Output format for analysis results"
)
@click.option(
    "--disable-llm",
    is_flag=True,
    default=False,
    help="Disable LLM-powered analysis (use rule-based only)"
)
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai", "anthropic"]),
    help="Specific LLM provider to use"
)
@click.option(
    "--generate-reports",
    is_flag=True,
    default=False,
    help="Generate comprehensive HTML reports"
)
@click.option(
    "--no-interactive",
    is_flag=True,
    default=False,
    help="Skip interactive AI assistant mode"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--skip-comprehensive",
    is_flag=True,
    default=False,
    help="Skip comprehensive analysis if recent results exist"
)
@click.option(
    "--force-rerun",
    is_flag=True,
    default=False,
    help="Force re-run of comprehensive analysis even if recent results exist"
)
def main(
    input_dir: Path,
    output_dir: Path,
    format: str,
    disable_llm: bool,
    llm_provider: str,
    generate_reports: bool,
    no_interactive: bool,
    verbose: bool,
    skip_comprehensive: bool,
    force_rerun: bool
):
    """LZA Diff Analyzer - Analyze CloudFormation diff logs with AI assistance"""
    
    # Run the async workflow
    try:
        asyncio.run(_run_analysis_workflow(
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=format,
            enable_llm=not disable_llm,
            llm_provider=llm_provider,
            generate_reports=generate_reports,
            no_interactive=no_interactive,
            verbose=verbose,
            skip_comprehensive=skip_comprehensive,
            force_rerun=force_rerun
        ))
    except KeyboardInterrupt:
        console.print("\n👋 Analysis interrupted by user")
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())


async def _run_analysis_workflow(
    input_dir: Path,
    output_dir: Path,
    output_format: str,
    enable_llm: bool,
    llm_provider: str,
    generate_reports: bool,
    no_interactive: bool,
    verbose: bool,
    skip_comprehensive: bool,
    force_rerun: bool
):
    """Run the complete analysis workflow"""
    
    from ..parsers.file_utils import FileManager
    from rich.prompt import Confirm
    
    # Step 1: Check if we can skip comprehensive analysis
    should_skip_analysis = False
    comprehensive_results = None
    
    if not force_rerun:
        analysis_state = FileManager.check_analysis_state(input_dir, output_dir)
        
        if analysis_state['has_previous_analysis']:
            console.print(f"\n[bold cyan]Previous Analysis Found:[/bold cyan]")
            for rec in analysis_state['recommendations']:
                console.print(f"  • {rec}")
        
        if skip_comprehensive and analysis_state['can_skip']:
            console.print(f"\n[green]✓[/green] [bold]Skipping comprehensive analysis - loading existing results[/bold]")
            loaded_results = FileManager.load_existing_analysis(output_dir)
            
            if loaded_results:
                comprehensive_results = loaded_results
                should_skip_analysis = True
                console.print(f"[green]✓[/green] Loaded existing analysis results")
            else:
                console.print(f"[yellow]⚠[/yellow] Failed to load existing results, proceeding with full analysis")
        elif analysis_state['can_skip'] and not skip_comprehensive:
            console.print(f"\n[bold yellow]Tip:[/bold yellow] Add --skip-comprehensive to use existing results and save time")
            
            # Interactive prompt when existing results can be reused
            if Confirm.ask("\n[bold cyan]Skip comprehensive analysis and use existing results?[/bold cyan]", default=True):
                console.print(f"\n[green]✓[/green] [bold]Skipping comprehensive analysis - loading existing results[/bold]")
                loaded_results = FileManager.load_existing_analysis(output_dir)
                
                if loaded_results:
                    comprehensive_results = loaded_results
                    should_skip_analysis = True
                    console.print(f"[green]✓[/green] Loaded existing analysis results")
                else:
                    console.print(f"[yellow]⚠[/yellow] Failed to load existing results, proceeding with full analysis")
            else:
                console.print(f"\n[blue]ℹ[/blue] Running fresh comprehensive analysis...")
    
    if force_rerun:
        console.print(f"\n[bold yellow]Force re-run enabled - ignoring existing results[/bold yellow]")
    
    # Step 2: Run analysis if not skipped
    if not should_skip_analysis:
        runner = AnalysisRunner(console)
        comprehensive_results = await runner.run_analysis(
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=output_format,
            enable_llm=enable_llm,
            llm_provider=llm_provider,
            verbose=verbose
        )
        
        if not comprehensive_results:
            console.print("[red]Analysis failed[/red]")
            return
    else:
        # Step 2a: Show analysis summary for loaded results
        console.print("\n" + "=" * 60)
        console.print("📊 [bold blue]Analysis Summary (From Previous Run)[/bold blue]")
        _show_analysis_summary(comprehensive_results, verbose)
        console.print("=" * 60)
    
    if not comprehensive_results:
        console.print("[red]Analysis failed[/red]")
        return
    
    # Step 2: Generate reports if requested
    if generate_reports:
        from ..parsers.file_utils import FileManager
        output_paths = FileManager.create_output_structure(output_dir)
        
        report_gen = ReportGenerator(console)
        report_gen.generate_reports(comprehensive_results, output_paths)
    
    # Step 3: Interactive session if not disabled
    if not no_interactive:
        await _start_interactive_session(
            comprehensive_results=comprehensive_results,
            input_dir=input_dir,
            llm_provider=llm_provider
        )


async def _start_interactive_session(
    comprehensive_results,
    input_dir: Path,
    llm_provider: str
):
    """Start interactive AI assistant session"""
    from rich.prompt import Confirm
    from ..interactive.simple_session import SimpleInteractiveSession
    
    # Simple transition
    console.print("\n" + "=" * 60)
    console.print("✅ [bold green]Analysis Complete![/bold green]")
    
    # Show quick summary
    try:
        if hasattr(comprehensive_results, 'input_analysis'):
            analysis = comprehensive_results.input_analysis
            stacks = getattr(analysis, 'total_stacks', 0)
            resources = getattr(analysis, 'total_resources_changed', 0)
            iam_changes = getattr(analysis, 'total_iam_changes', 0)
            console.print(f"📊 {stacks} stacks, {resources} resources, {iam_changes} IAM changes analyzed")
        else:
            console.print("📊 Analysis completed successfully")
    except:
        console.print("📊 Analysis data processed")
    
    console.print()
    
    # Ask for interactive session
    if Confirm.ask("🤖 Start AI assistant for detailed exploration?", default=True):
        console.print("\n🚀 Starting AI Assistant...")
        
        session = SimpleInteractiveSession(console)
        try:
            await session.start(str(input_dir), comprehensive_results)
        except KeyboardInterrupt:
            console.print("\n👋 Session ended")
        except Exception as e:
            console.print(f"[red]Session error: {e}[/red]")
    else:
        console.print("\n💾 Results saved. Re-run anytime to access the assistant.")


def _show_analysis_summary(comprehensive_results, verbose: bool):
    """Show analysis summary for loaded results"""
    try:
        from ..formatters.admin_friendly import AdminFriendlyFormatter
        
        if not comprehensive_results:
            console.print("[yellow]No analysis results to display[/yellow]")
            return
        
        # Create a minimal diff_analysis object for the formatter
        # Since we're loading existing results, we may not have the full diff_analysis
        diff_analysis = None
        
        # Handle both dict and object formats
        if isinstance(comprehensive_results, dict):
            input_analysis = comprehensive_results.get('input_analysis')
        elif hasattr(comprehensive_results, 'input_analysis'):
            input_analysis = comprehensive_results.input_analysis
        else:
            input_analysis = getattr(comprehensive_results, 'input_analysis', None)
        
        if input_analysis:
            try:
                # Create a simple object with the basic stats
                class BasicDiffAnalysis:
                    def __init__(self, input_analysis):
                        if hasattr(input_analysis, 'total_stacks'):
                            self.total_stacks = input_analysis.total_stacks
                            self.total_resources_changed = input_analysis.total_resources_changed
                            self.total_iam_changes = input_analysis.total_iam_changes
                        elif isinstance(input_analysis, dict):
                            # Handle dict format
                            self.total_stacks = input_analysis.get('total_stacks', 0)
                            self.total_resources_changed = input_analysis.get('total_resources_changed', 0)
                            self.total_iam_changes = input_analysis.get('total_iam_changes', 0)
                        else:
                            self.total_stacks = 0
                            self.total_resources_changed = 0
                            self.total_iam_changes = 0
                        # Add empty lists for compatibility
                        self.stack_diffs = []
                
                diff_analysis = BasicDiffAnalysis(input_analysis)
            except Exception as e:
                console.print(f"[yellow]Could not extract diff analysis: {e}[/yellow]")
        
        if verbose:
            # Show technical summary for verbose mode
            _show_technical_summary(comprehensive_results, diff_analysis)
        else:
            # Show admin-friendly summary by default
            formatter = AdminFriendlyFormatter(console)
            formatter.format_summary(comprehensive_results, diff_analysis, True)
            
    except Exception as e:
        console.print(f"[red]Analysis summary failed: {e}[/red]")
        console.print("[yellow]Proceeding without summary display[/yellow]")


def _show_technical_summary(comprehensive_results, diff_analysis):
    """Show technical summary for verbose mode"""
    console.print("\n[bold]=== LOADED ANALYSIS SUMMARY ===[/bold]")
    
    # Basic stats
    if diff_analysis:
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Stacks analyzed: {diff_analysis.total_stacks}")
        console.print(f"  Resource changes: {diff_analysis.total_resources_changed}")
        console.print(f"  IAM changes: {diff_analysis.total_iam_changes}")
    
    # Risk summary
    if hasattr(comprehensive_results, 'rule_based_analysis'):
        rule_analysis = comprehensive_results.rule_based_analysis
    else:
        rule_analysis = comprehensive_results.get('rule_based_analysis', {})
    
    if rule_analysis:
        console.print(f"\n[bold]Risk Assessment:[/bold]")
        risk_level = rule_analysis.get('overall_risk_level', 'Unknown')
        total_findings = rule_analysis.get('total_findings', 0)
        
        console.print(f"  Overall risk: {risk_level}")
        console.print(f"  Total findings: {total_findings}")
        console.print(f"    Critical: {rule_analysis.get('critical_count', 0)}")
        console.print(f"    High: {rule_analysis.get('high_count', 0)}")
        console.print(f"    Medium: {rule_analysis.get('medium_count', 0)}")
        console.print(f"    Low: {rule_analysis.get('low_count', 0)}")
    
    # Analysis metadata
    if hasattr(comprehensive_results, 'metadata'):
        metadata = comprehensive_results.metadata
        analysis_id = comprehensive_results.analysis_id
    else:
        metadata = comprehensive_results.get("metadata", {})
        analysis_id = comprehensive_results.get('analysis_id', 'Unknown')
        
    if metadata:
        console.print(f"\n[bold]Analysis Details:[/bold]")
        if isinstance(metadata, dict):
            console.print(f"  Analyzers used: {', '.join(metadata.get('analyzers_used', []))}")
            console.print(f"  LLM enabled: {metadata.get('llm_enabled', False)}")
        console.print(f"  Analysis ID: {analysis_id}")


if __name__ == "__main__":
    main()