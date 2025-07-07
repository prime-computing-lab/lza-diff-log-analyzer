"""
Analysis runner module - handles the core analysis workflow
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..parsers.diff_parser import DiffParser
from ..parsers.file_utils import FileValidator, FileManager
from ..analyzers.analysis_engine import ComprehensiveAnalysisEngine
from ..core.errors import (
    ValidationError, ParseError, AnalysisError, LZAError, 
    ErrorHandler, handle_cli_errors
)


class AnalysisRunner:
    """Handles the complete analysis workflow"""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def run_analysis(
        self, 
        input_dir: Path, 
        output_dir: Path, 
        output_format: str,
        enable_llm: bool = True,
        llm_provider: Optional[str] = None,
        verbose: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Run complete analysis workflow
        
        Returns:
            Analysis results or None if failed
        """
        
        # Step 1: Validate input
        validation_result = self._validate_input(input_dir)
        if not validation_result['is_valid']:
            return None
            
        # Step 2: Create output structure
        output_paths = FileManager.create_output_structure(output_dir)
        
        # Step 3: Parse diff files
        diff_analysis = self._parse_files(input_dir, validation_result['file_count'])
        if not diff_analysis:
            return None
            
        # Step 4: Run comprehensive analysis
        comprehensive_results = await self._run_comprehensive_analysis(
            diff_analysis, enable_llm, llm_provider, verbose
        )
        if not comprehensive_results:
            return None
            
        # Step 5: Save results
        success = self._save_results(
            comprehensive_results, diff_analysis, output_paths, output_format
        )
        
        if success:
            self._show_completion_summary(comprehensive_results, output_paths, verbose)
            return comprehensive_results
        else:
            self.console.print("[red]Failed to save results[/red]")
            return None
    
    def _validate_input(self, input_dir: Path) -> Dict[str, Any]:
        """Validate input directory"""
        self.console.print(f"[bold blue]Validating input directory: {input_dir}[/bold blue]")
        
        try:
            # Validate path exists
            ErrorHandler.validate_path(input_dir, "input directory", must_exist=True)
            
            validation_result = FileValidator.validate_directory(input_dir)
            
            if not validation_result['is_valid']:
                errors = validation_result.get('errors', [])
                error_msg = f"Input validation failed: {'; '.join(errors)}"
                raise ValidationError(error_msg, details={"errors": errors})
                
            if validation_result['warnings']:
                self.console.print("[yellow]Warnings:[/yellow]")
                for warning in validation_result['warnings']:
                    self.console.print(f"  [yellow]⚠[/yellow] {warning}")
            
            self.console.print(f"✅ Found {validation_result['file_count']} diff files")
            return validation_result
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValidationError(f"Input validation failed: {e}", cause=e)
    
    def _parse_files(self, input_dir: Path, file_count: int):
        """Parse diff files"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            parse_task = progress.add_task("Parsing diff logs...", total=file_count)
            
            try:
                parser = DiffParser()
                diff_analysis = parser.parse_directory(input_dir)
                progress.update(parse_task, completed=file_count)
                return diff_analysis
            except Exception as e:
                self.console.print(f"[red]Parsing failed: {e}[/red]")
                return None
    
    async def _run_comprehensive_analysis(
        self, 
        diff_analysis, 
        enable_llm: bool, 
        llm_provider: Optional[str],
        verbose: bool
    ):
        """Run comprehensive analysis"""
        try:
            analysis_engine = ComprehensiveAnalysisEngine()
            
            if verbose:
                self.console.print("🔍 Running comprehensive analysis...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                analysis_task = progress.add_task(
                    "Running analysis..." if not enable_llm 
                    else "Running AI-powered analysis...", 
                    total=None
                )
                
                comprehensive_results = await analysis_engine.analyze(
                    diff_analysis,
                    enable_llm=enable_llm,
                    llm_provider=llm_provider
                )
                
                progress.update(analysis_task, completed=True)
                
            return comprehensive_results
            
        except Exception as e:
            self.console.print(f"[red]Analysis failed: {e}[/red]")
            if verbose:
                import traceback
                self.console.print(traceback.format_exc())
            return None
    
    def _save_results(
        self, 
        comprehensive_results, 
        diff_analysis, 
        output_paths: Dict[str, Path], 
        output_format: str
    ) -> bool:
        """Save analysis results"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            save_task = progress.add_task("Saving results...", total=None)
            
            try:
                # Save comprehensive results
                results_file = output_paths['analysis'] / f"comprehensive_analysis.{output_format}"
                success = FileManager.save_analysis(comprehensive_results, results_file, output_format)
                
                # Save basic diff analysis for backward compatibility
                basic_file = output_paths['analysis'] / f"diff_analysis.{output_format}"
                basic_success = FileManager.save_analysis(diff_analysis, basic_file, output_format)
                
                progress.remove_task(save_task)
                return success and basic_success
                
            except Exception as e:
                progress.remove_task(save_task)
                self.console.print(f"[red]Save failed: {e}[/red]")
                return False
    
    def _show_completion_summary(
        self, 
        comprehensive_results, 
        output_paths: Dict[str, Path], 
        verbose: bool
    ):
        """Show completion summary"""
        results_file = output_paths['analysis'] / "comprehensive_analysis.json"
        basic_file = output_paths['analysis'] / "diff_analysis.json"
        
        self.console.print("[green]✓[/green] Analysis complete!")
        self.console.print(f"  Main results: {results_file}")
        self.console.print(f"  Basic analysis: {basic_file}")
        
        if verbose:
            self._show_technical_summary(comprehensive_results)
        else:
            self._show_admin_summary(comprehensive_results)
    
    def _show_admin_summary(self, comprehensive_results):
        """Show admin-friendly summary"""
        from ..formatters.admin_friendly import AdminFriendlyFormatter
        
        formatter = AdminFriendlyFormatter(self.console)
        formatter.format_summary(comprehensive_results, None, True)
    
    def _show_technical_summary(self, comprehensive_results):
        """Show technical summary for verbose mode"""
        # Extract key metrics
        if hasattr(comprehensive_results, 'input_analysis'):
            input_analysis = comprehensive_results.input_analysis
            rule_analysis = comprehensive_results.rule_based_analysis or {}
        else:
            # Handle backward compatibility with dictionary format
            if hasattr(comprehensive_results, 'get'):
                input_analysis = comprehensive_results.get('input_analysis', {})
                rule_analysis = comprehensive_results.get('rule_based_analysis', {})
            else:
                input_analysis = getattr(comprehensive_results, 'input_analysis', {})
                rule_analysis = getattr(comprehensive_results, 'rule_based_analysis', {})
        
        self.console.print("\n[bold]=== ANALYSIS SUMMARY ===[/bold]")
        
        # Basic stats
        total_stacks = getattr(input_analysis, 'total_stacks', 0) if hasattr(input_analysis, 'total_stacks') else input_analysis.get('total_stacks', 0)
        total_resources = getattr(input_analysis, 'total_resources_changed', 0) if hasattr(input_analysis, 'total_resources_changed') else input_analysis.get('total_resources_changed', 0)
        total_iam = getattr(input_analysis, 'total_iam_changes', 0) if hasattr(input_analysis, 'total_iam_changes') else input_analysis.get('total_iam_changes', 0)
        
        self.console.print(f"\n[bold]Statistics:[/bold]")
        self.console.print(f"  Stacks analyzed: {total_stacks}")
        self.console.print(f"  Resource changes: {total_resources}")
        self.console.print(f"  IAM changes: {total_iam}")
        
        # Risk summary
        if rule_analysis:
            risk_level = rule_analysis.get('overall_risk_level', 'Unknown')
            total_findings = rule_analysis.get('total_findings', 0)
            
            self.console.print(f"\n[bold]Risk Assessment:[/bold]")
            self.console.print(f"  Overall risk: {risk_level}")
            self.console.print(f"  Total findings: {total_findings}")


class ReportGenerator:
    """Handles report generation workflow"""
    
    def __init__(self, console: Console):
        self.console = console
        
    def generate_reports(
        self, 
        comprehensive_results, 
        output_paths: Dict[str, Path]
    ) -> Dict[str, Path]:
        """Generate comprehensive reports"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            report_task = progress.add_task("Generating reports...", total=None)
            
            try:
                from ..reports.report_generator import AdminReportGenerator
                
                report_generator = AdminReportGenerator()
                report_files = report_generator.save_reports(
                    comprehensive_results,
                    output_paths['analysis'] / 'reports',
                    formats=['html']
                )
                
                progress.remove_task(report_task)
                
                if report_files:
                    self.console.print(f"\n[bold]Generated Reports:[/bold]")
                    for report_name, file_path in report_files.items():
                        self.console.print(f"  📊 {report_name}: {file_path}")
                
                return report_files
                
            except Exception as e:
                progress.remove_task(report_task)
                self.console.print(f"[yellow]Report generation failed: {e}[/yellow]")
                return {}