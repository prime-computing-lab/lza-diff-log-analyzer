"""
Ollama client implementation with error handling
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, AsyncIterator, Optional
from .base import BaseLLMProvider, LLMProvider, LLMMessage, LLMResponse, LLMConfig, LLMError


class OllamaClient(BaseLLMProvider):
    """Ollama client for local LLM inference"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.session: Optional[aiohttp.ClientSession] = None
        self._availability_error: Optional[str] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _format_messages_for_ollama(self, messages: List[LLMMessage]) -> str:
        """Format messages for Ollama's chat completion format"""
        formatted = []
        for msg in messages:
            if msg.role == "system":
                formatted.append(f"System: {msg.content}")
            elif msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
        
        formatted.append("Assistant:")
        return "\n\n".join(formatted)
    
    async def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Generate a response from Ollama"""
        try:
            session = await self._get_session()
            
            # Prepare request payload
            payload = {
                "model": self.config.model,
                "prompt": self._format_messages_for_ollama(messages),
                "stream": False,
                "options": {
                    "temperature": self.config.temperature
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            # Add additional parameters if provided
            if self.config.additional_params:
                payload["options"].update(self.config.additional_params)
            
            # Make request to Ollama
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(
                        f"Ollama API error (status {response.status}): {error_text}",
                        LLMProvider.OLLAMA
                    )
                
                result = await response.json()
                
                return LLMResponse(
                    content=result.get("response", ""),
                    provider=LLMProvider.OLLAMA,
                    model=self.config.model,
                    finish_reason=result.get("done_reason"),
                    token_usage={
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                    },
                    metadata={
                        "eval_duration_ms": result.get("eval_duration", 0) // 1000000,
                        "total_duration_ms": result.get("total_duration", 0) // 1000000
                    }
                )
        
        except aiohttp.ClientError as e:
            raise LLMError(
                f"Network error connecting to Ollama: {str(e)}",
                LLMProvider.OLLAMA,
                e
            )
        except json.JSONDecodeError as e:
            raise LLMError(
                f"Invalid JSON response from Ollama: {str(e)}",
                LLMProvider.OLLAMA,
                e
            )
        except Exception as e:
            # Enhanced error diagnostics
            error_details = self._diagnose_error(e)
            raise LLMError(
                f"Unexpected error with Ollama: {error_details}",
                LLMProvider.OLLAMA,
                e
            )
    
    async def stream_generate(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Generate a streaming response from Ollama"""
        try:
            session = await self._get_session()
            
            payload = {
                "model": self.config.model,
                "prompt": self._format_messages_for_ollama(messages),
                "stream": True,
                "options": {
                    "temperature": self.config.temperature
                }
            }
            
            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens
            
            if self.config.additional_params:
                payload["options"].update(self.config.additional_params)
            
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(
                        f"Ollama streaming API error (status {response.status}): {error_text}",
                        LLMProvider.OLLAMA
                    )
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
        
        except aiohttp.ClientError as e:
            raise LLMError(
                f"Network error during Ollama streaming: {str(e)}",
                LLMProvider.OLLAMA,
                e
            )
        except Exception as e:
            # Enhanced error diagnostics for streaming
            error_details = self._diagnose_error(e)
            raise LLMError(
                f"Unexpected error during Ollama streaming: {error_details}",
                LLMProvider.OLLAMA,
                e
            )
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            import asyncio
            import aiohttp
            
            # Try to get current event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, create a task
                task = asyncio.create_task(self._check_availability())
                # Run in thread pool to avoid blocking
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._check_availability())
                    return future.result(timeout=5)
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                return asyncio.run(self._check_availability())
                
        except Exception:
            # Fallback to synchronous check
            try:
                import requests
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = [model.get("name", "") for model in data.get("models", [])]
                    return self.config.model in models
                return False
            except Exception:
                return False
    
    async def _check_availability(self) -> bool:
        """Async availability check with detailed diagnostics"""
        session = None
        try:
            # Use a temporary session for availability check to avoid conflicts
            timeout = aiohttp.ClientTimeout(total=5)
            session = aiohttp.ClientSession(timeout=timeout)
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model.get("name", "") for model in data.get("models", [])]
                    model_available = self.config.model in models
                    
                    if not model_available:
                        # Store diagnostic information for later use
                        available_models = ", ".join(models[:5])  # Show first 5 models
                        self._availability_error = (
                            f"Model '{self.config.model}' not found. "
                            f"Available models: {available_models}. "
                            f"Run: ollama pull {self.config.model}"
                        )
                    
                    return model_available
                else:
                    self._availability_error = f"Ollama API returned status {response.status}"
                    return False
        except aiohttp.ClientConnectorError:
            self._availability_error = (
                "Cannot connect to Ollama service. "
                "Make sure Ollama is running with: ollama serve"
            )
            return False
        except asyncio.TimeoutError:
            self._availability_error = (
                "Ollama service is not responding (timeout). "
                "Check if the service is overloaded or restart it"
            )
            return False
        except Exception as e:
            self._availability_error = f"Unexpected error: {str(e)}"
            return False
        finally:
            if session and not session.closed:
                await session.close()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            import asyncio
            return asyncio.run(self._get_model_info())
        except Exception:
            return {
                "model": self.config.model,
                "provider": "ollama",
                "available": False,
                "error": "Could not retrieve model information"
            }
    
    async def _get_model_info(self) -> Dict[str, Any]:
        """Async model info retrieval"""
        session = None
        try:
            # Use a temporary session for model info to avoid conflicts
            timeout = aiohttp.ClientTimeout(total=10)
            session = aiohttp.ClientSession(timeout=timeout)
            
            # Get model details
            async with session.post(
                f"{self.base_url}/api/show",
                json={"name": self.config.model}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "model": self.config.model,
                        "provider": "ollama",
                        "available": True,
                        "size": data.get("size", "unknown"),
                        "family": data.get("details", {}).get("family", "unknown"),
                        "parameter_size": data.get("details", {}).get("parameter_size", "unknown"),
                        "quantization_level": data.get("details", {}).get("quantization_level", "unknown")
                    }
                else:
                    return {
                        "model": self.config.model,
                        "provider": "ollama",
                        "available": False,
                        "error": f"Model not found (status {response.status})"
                    }
        
        except Exception as e:
            return {
                "model": self.config.model,
                "provider": "ollama",
                "available": False,
                "error": str(e)
            }
        finally:
            if session and not session.closed:
                await session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    def _diagnose_error(self, error: Exception) -> str:
        """Provide detailed error diagnosis and troubleshooting suggestions"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Connection-related errors
        if "connection" in error_str or "refused" in error_str:
            return (f"{error} - Ollama service may not be running. "
                   f"Try: 'ollama serve' to start the service")
        
        # Timeout errors
        if "timeout" in error_str or error_type == "TimeoutError":
            return (f"{error} - Request timed out. The model '{self.config.model}' "
                   f"may be too large or system is under load. Try a smaller model or increase timeout")
        
        # Model not found errors
        if "not found" in error_str or "404" in error_str:
            return (f"{error} - Model '{self.config.model}' not found. "
                   f"Try: 'ollama pull {self.config.model}' to download the model")
        
        # Memory/resource errors
        if "memory" in error_str or "out of memory" in error_str:
            return (f"{error} - Insufficient memory to run model '{self.config.model}'. "
                   f"Try a smaller model like 'qwen2.5:7b' or free up system memory")
        
        # Network connectivity issues
        if "network" in error_str or "unreachable" in error_str:
            return (f"{error} - Network connectivity issue. "
                   f"Check if Ollama is accessible at {self.base_url}")
        
        # Permission errors
        if "permission" in error_str or "unauthorized" in error_str:
            return (f"{error} - Permission denied. "
                   f"Check Ollama service permissions and configuration")
        
        # JSON/parsing errors
        if "json" in error_str or "parse" in error_str:
            return (f"{error} - Invalid response format from Ollama. "
                   f"The model may be corrupted or incompatible")
        
        # Async context errors
        if "event loop" in error_str or "coroutine" in error_str:
            return (f"{error} - Async context issue. "
                   f"This is likely a programming error in the async handling")
        
        # Default case with troubleshooting steps
        troubleshooting_steps = [
            "1. Check if Ollama is running: 'ollama serve'",
            f"2. Verify model is available: 'ollama list' (looking for {self.config.model})",
            f"3. If missing, download model: 'ollama pull {self.config.model}'",
            f"4. Test model directly: 'ollama run {self.config.model} \"Hello\"'",
            f"5. Check Ollama logs for detailed error information"
        ]
        
        return (f"{error} - Troubleshooting steps: " + " | ".join(troubleshooting_steps))
    
    def get_availability_error(self) -> Optional[str]:
        """Get detailed error message from the last availability check"""
        return getattr(self, '_availability_error', None)