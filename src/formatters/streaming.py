"""
Streaming UI components for displaying LLM thinking and responses in real-time
"""

import asyncio
import time
from typing import Optional, Callable, AsyncIterator
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn


class StreamingDisplay:
    """Handles real-time display of LLM streaming responses"""
    
    def __init__(self, console: Console):
        self.console = console
        self.current_text = ""
        self.is_streaming = False
        self.analysis_context = None  # Store analysis context for better responses
        
    async def stream_text(
        self, 
        text_stream: AsyncIterator[str], 
        title: str = "AI Assistant",
        prefix: str = "🤔 ",
        show_cursor: bool = True
    ):
        """
        Display streaming text with a typewriter effect
        
        Args:
            text_stream: Async iterator of text chunks
            title: Panel title to display
            prefix: Text prefix (e.g., thinking emoji)
            show_cursor: Whether to show a blinking cursor
        """
        self.current_text = ""
        self.is_streaming = True
        cursor = "▌" if show_cursor else ""
        
        with Live(
            self._create_panel(prefix + cursor, title),
            console=self.console,
            refresh_per_second=10
        ) as live:
            try:
                async for chunk in text_stream:
                    if chunk:
                        self.current_text += chunk
                        display_text = prefix + self.current_text
                        if show_cursor:
                            display_text += cursor
                        live.update(self._create_panel(display_text, title))
                        
                        # Small delay for better reading experience
                        await asyncio.sleep(0.05)
                
                # Final update without cursor
                final_text = prefix + self.current_text
                live.update(self._create_panel(final_text, title))
                
            except Exception as e:
                error_text = f"{prefix}Error during streaming: {str(e)}"
                live.update(self._create_panel(error_text, title, style="red"))
            finally:
                self.is_streaming = False
    
    def _create_panel(self, text: str, title: str, style: str = "blue") -> Panel:
        """Create a Rich panel for the streaming text"""
        return Panel(
            Text(text, style="white"),
            title=f"💭 {title}",
            border_style=style,
            padding=(1, 2)
        )


class ProgressWithStreaming:
    """Enhanced progress display that can show both progress bars and streaming text"""
    
    def __init__(self, console: Console):
        self.console = console
        self.progress = None
        self.streaming_display = StreamingDisplay(console)
        
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        self.progress.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
    
    def add_task(self, description: str, total: Optional[float] = None) -> int:
        """Add a progress task"""
        if self.progress:
            return self.progress.add_task(description, total=total)
        return 0
    
    def update_task(self, task_id: int, description: Optional[str] = None, advance: Optional[float] = None):
        """Update a progress task"""
        if self.progress:
            kwargs = {}
            if description is not None:
                kwargs['description'] = description
            if advance is not None:
                kwargs['advance'] = advance
            self.progress.update(task_id, **kwargs)
    
    def complete_task(self, task_id: int):
        """Mark a task as complete"""
        if self.progress:
            self.progress.update(task_id, completed=True)
    
    async def stream_during_task(
        self,
        task_id: int,
        text_stream: AsyncIterator[str],
        analysis_type: str = "Analysis"
    ):
        """Stream text while showing progress for a task"""
        # Update task to show streaming status
        self.update_task(task_id, f"🧠 {analysis_type} (streaming...)")
        
        # Create a separate live display for streaming below the progress
        stream_content = ""
        
        with Live(
            self._create_streaming_panel("", analysis_type),
            console=self.console,
            refresh_per_second=8
        ) as live:
            try:
                async for chunk in text_stream:
                    if chunk:
                        stream_content += chunk
                        # Show last few words to give sense of progress
                        display_content = self._get_recent_content(stream_content)
                        live.update(self._create_streaming_panel(display_content, analysis_type))
                        await asyncio.sleep(0.1)
                
                # Final update
                final_content = self._get_recent_content(stream_content, final=True)
                live.update(self._create_streaming_panel(final_content, analysis_type))
                
                # Mark task as complete
                self.update_task(task_id, f"✅ {analysis_type} complete")
                
            except Exception as e:
                self.update_task(task_id, f"❌ {analysis_type} failed: {str(e)}")
                live.update(self._create_streaming_panel(f"Error: {str(e)}", analysis_type, "red"))
    
    def _create_streaming_panel(self, content: str, analysis_type: str, style: str = "green") -> Panel:
        """Create panel for streaming content"""
        if not content:
            content = "🤔 Thinking..."
        
        return Panel(
            Text(content, style="white"),
            title=f"🧠 AI {analysis_type}",
            border_style=style,
            height=4,
            padding=(0, 1)
        )
    
    def _get_recent_content(self, full_content: str, final: bool = False, max_chars: int = 100) -> str:
        """Get recent content for display, showing last few words/sentences"""
        if not full_content:
            return "🤔 Thinking..."
        
        if final:
            # For final display, show a summary or first few lines
            lines = full_content.split('\n')
            summary_lines = []
            for line in lines[:3]:
                if line.strip():
                    summary_lines.append(line.strip())
            return '\n'.join(summary_lines) if summary_lines else full_content[:max_chars]
        
        # For streaming, show the most recent content
        if len(full_content) <= max_chars:
            return full_content
        
        # Try to break at word boundaries
        recent = full_content[-max_chars:]
        first_space = recent.find(' ')
        if first_space > 0:
            recent = recent[first_space:].strip()
        
        return "..." + recent


class MultiStepStreamingProgress:
    """Handles progress display for multi-step LLM analysis with streaming"""
    
    def __init__(self, console: Console):
        self.console = console
        self.progress_display = ProgressWithStreaming(console)
        self.analysis_steps = [
            "Overall Assessment",
            "Network Impact Analysis", 
            "Security Impact Analysis",
            "Operational Readiness"
        ]
    
    async def run_multi_step_analysis(
        self,
        analysis_functions: list,
        enable_streaming: bool = True
    ):
        """
        Run multiple analysis steps with progress and optional streaming
        
        Args:
            analysis_functions: List of async functions that return either:
                - AsyncIterator[str] for streaming
                - str for non-streaming results
            enable_streaming: Whether to use streaming display
        """
        with self.progress_display as progress:
            results = []
            
            for i, (analysis_func, step_name) in enumerate(zip(analysis_functions, self.analysis_steps)):
                task_id = progress.add_task(f"🔄 {step_name}...", total=1)
                
                try:
                    result = await analysis_func()
                    
                    # Check if result is a streaming iterator
                    if hasattr(result, '__aiter__') and enable_streaming:
                        await progress.stream_during_task(task_id, result, step_name)
                        # Collect all chunks for final result
                        full_result = ""
                        async for chunk in result:
                            full_result += chunk
                        results.append(full_result)
                    else:
                        # Non-streaming result
                        progress.update_task(task_id, f"✅ {step_name} complete", advance=1)
                        results.append(str(result))
                        
                except Exception as e:
                    progress.update_task(task_id, f"❌ {step_name} failed")
                    results.append(f"Error: {str(e)}")
            
            return results


class ThinkingIndicator:
    """Simple thinking indicator with customizable messages"""
    
    def __init__(self, console: Console):
        self.console = console
        self.spinner = Spinner("dots", text="🤔 Thinking...")
        
    def show(self, message: str = "🤔 Thinking..."):
        """Show a thinking indicator with custom message"""
        self.spinner.text = message
        
    def show_with_context(self, analysis_type: str, model_name: str = ""):
        """Show thinking indicator with analysis context"""
        model_info = f" ({model_name})" if model_name else ""
        message = f"🧠 Analyzing {analysis_type.lower()}{model_info}..."
        self.show(message)
        
    async def show_timed(self, message: str = "🤔 Thinking...", duration: float = 2.0):
        """Show thinking indicator for a specific duration"""
        with Live(
            Panel(Text(message, style="yellow"), title="💭 AI Assistant", border_style="blue"),
            console=self.console,
            refresh_per_second=2
        ):
            await asyncio.sleep(duration)


# Utility functions for easy integration

async def stream_llm_response(
    console: Console,
    response_stream: AsyncIterator[str],
    title: str = "AI Analysis",
    show_progress: bool = True
) -> str:
    """
    Utility function to stream an LLM response with progress indication
    
    Returns:
        The complete response text
    """
    display = StreamingDisplay(console)
    await display.stream_text(response_stream, title=title)
    return display.current_text


def create_analysis_progress(console: Console) -> MultiStepStreamingProgress:
    """Create a multi-step analysis progress display"""
    return MultiStepStreamingProgress(console)


class TransitionDisplay:
    """Handles the transition from analysis to interactive mode"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def show_analysis_complete(self, comprehensive_results, analysis_summary: str = None):
        """Show analysis completion with summary"""
        from rich.panel import Panel
        from rich.text import Text
        
        # Create a summary panel
        if analysis_summary:
            summary_text = analysis_summary
        else:
            summary_text = self._generate_quick_summary(comprehensive_results)
        
        completion_panel = Panel(
            Text(summary_text, style="white"),
            title="✅ Analysis Complete",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(completion_panel)
    
    def show_transition_prompt(self):
        """Show the transition prompt to interactive mode"""
        from rich.panel import Panel
        from rich.text import Text
        
        transition_text = """🤖 Your LZA analysis is ready for exploration!

I can now help you:
• Dive deep into specific risks and findings
• Explain complex IAM or networking changes  
• Plan your deployment and testing strategy
• Answer questions about specific stacks or files

Ready to explore your analysis together? (y/n)"""
        
        prompt_panel = Panel(
            Text(transition_text, style="cyan"),
            title="🚀 AI Assistant Ready",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(prompt_panel)
        self.console.print()
    
    def _generate_quick_summary(self, comprehensive_results) -> str:
        """Generate a quick summary of analysis results"""
        try:
            # Extract key metrics from comprehensive results
            if hasattr(comprehensive_results, 'input_analysis'):
                input_analysis = comprehensive_results.input_analysis
                total_stacks = input_analysis.total_stacks if hasattr(input_analysis, 'total_stacks') else 0
                total_resources = input_analysis.total_resources_changed if hasattr(input_analysis, 'total_resources_changed') else 0
                total_iam = input_analysis.total_iam_changes if hasattr(input_analysis, 'total_iam_changes') else 0
            else:
                # Fallback for dict format
                if hasattr(comprehensive_results, 'get'):
                    input_analysis = comprehensive_results.get('input_analysis', {})
                    total_stacks = input_analysis.get('total_stacks', 0)
                    total_resources = input_analysis.get('total_resources_changed', 0)
                    total_iam = input_analysis.get('total_iam_changes', 0)
                else:
                    input_analysis = getattr(comprehensive_results, 'input_analysis', {})
                    total_stacks = getattr(input_analysis, 'total_stacks', 0)
                    total_resources = getattr(input_analysis, 'total_resources_changed', 0)
                    total_iam = getattr(input_analysis, 'total_iam_changes', 0)
            
            # Extract risk assessment
            risk_info = ""
            if hasattr(comprehensive_results, 'rule_based_analysis'):
                rule_analysis = comprehensive_results.rule_based_analysis
            else:
                if hasattr(comprehensive_results, 'get'):
                    rule_analysis = comprehensive_results.get('rule_based_analysis', {})
                else:
                    rule_analysis = getattr(comprehensive_results, 'rule_based_analysis', {})
                
            if rule_analysis:
                risk_level = rule_analysis.get('overall_risk_level', 'Unknown')
                total_findings = rule_analysis.get('total_findings', 0)
                risk_info = f"\n🎯 Risk Level: {risk_level} ({total_findings} findings)"
            
            summary = f"""📊 Analysis Summary:
• {total_stacks} CloudFormation stacks analyzed
• {total_resources} resource changes identified  
• {total_iam} IAM permission changes{risk_info}

🧠 AI Assistant loaded with full analysis context and RAG access to your diff files."""
            
            return summary
            
        except Exception as e:
            return f"""📊 Analysis completed successfully!
            
🧠 AI Assistant ready with full context access to help you explore the results.

Note: Summary generation encountered an issue ({str(e)}), but all analysis data is available for exploration."""
    
    async def show_interactive_startup(self):
        """Show the interactive mode startup animation"""
        from rich.live import Live
        from rich.panel import Panel
        from rich.text import Text
        from rich.errors import LiveError
        import asyncio
        
        startup_messages = [
            "🔄 Initializing AI Assistant...",
            "🧠 Loading LZA expertise modules...", 
            "📁 Indexing diff files for RAG access...",
            "✅ Ready to assist with your analysis!"
        ]
        
        # Try to create Live display, fallback to simple print if there's a conflict
        try:
            # Use a single Live context for the entire animation
            panel = Panel(
                Text(startup_messages[0], style="yellow"),
                title="🤖 AI Assistant",
                border_style="blue",
                height=3
            )
            
            with Live(panel, console=self.console, refresh_per_second=10) as live:
                for i, message in enumerate(startup_messages):
                    panel = Panel(
                        Text(message, style="yellow" if i < len(startup_messages)-1 else "green"),
                        title="🤖 AI Assistant",
                        border_style="blue",
                        height=3
                    )
                    live.update(panel)
                    await asyncio.sleep(0.8)
        except LiveError:
            # Fallback to simple console prints if Live display conflicts
            for i, message in enumerate(startup_messages):
                panel = Panel(
                    Text(message, style="yellow" if i < len(startup_messages)-1 else "green"),
                    title="🤖 AI Assistant",
                    border_style="blue",
                    height=3
                )
                self.console.print(panel)
                await asyncio.sleep(0.8)
        
        self.console.print()


def create_transition_display(console: Console) -> TransitionDisplay:
    """Create a transition display for analysis to interactive mode"""
    return TransitionDisplay(console)