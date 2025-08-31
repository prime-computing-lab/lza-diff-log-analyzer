"""
Conversation Manager for AI Best Practices Aligned Chat Memory

This module implements modern conversation management following AI application best practices:
- Structured message history with role-based conversation flow
- Token-aware context management with intelligent truncation
- Configurable retention strategies and resource efficiency
- Message compression and semantic importance scoring
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import tiktoken
from pathlib import Path

from .base import LLMMessage, LLMConfig, LLMProvider


logger = logging.getLogger(__name__)


class RetentionStrategy(str, Enum):
    """Conversation retention strategies"""
    SLIDING_WINDOW = "sliding_window"
    SEMANTIC_COMPRESSION = "semantic_compression" 
    FIXED = "fixed"


class MessageImportance(str, Enum):
    """Message importance levels for retention priority"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConversationConfig:
    """Configuration for conversation management"""
    enabled: bool = True
    max_history_messages: int = 20
    max_history_tokens: int = 4000
    retention_strategy: RetentionStrategy = RetentionStrategy.SLIDING_WINDOW
    compression_threshold: float = 0.8
    include_system_messages: bool = False
    important_keywords: List[str] = field(default_factory=lambda: ["iam", "dependenciesstack", "security"])
    preserve_last_n_important: int = 5
    enable_token_counting: bool = True
    enable_compression: bool = False
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ConversationConfig':
        """Create configuration from dictionary"""
        # Handle nested conversation config
        conversation_config = config_dict.get('conversation', {})
        
        return cls(
            enabled=conversation_config.get('enabled', True),
            max_history_messages=conversation_config.get('max_history_messages', 20),
            max_history_tokens=conversation_config.get('max_history_tokens', 4000),
            retention_strategy=RetentionStrategy(
                conversation_config.get('retention_strategy', 'sliding_window')
            ),
            compression_threshold=conversation_config.get('compression_threshold', 0.8),
            include_system_messages=conversation_config.get('include_system_messages', False),
            important_keywords=conversation_config.get(
                'important_keywords', 
                ["iam", "dependenciesstack", "security"]
            ),
            preserve_last_n_important=conversation_config.get('preserve_last_n_important', 5),
            enable_token_counting=conversation_config.get('enable_token_counting', True),
            enable_compression=conversation_config.get('enable_compression', False)
        )


@dataclass
class MessageMetadata:
    """Enhanced metadata for conversation messages"""
    timestamp: datetime
    importance: MessageImportance = MessageImportance.MEDIUM
    token_count: int = 0
    contains_keywords: List[str] = field(default_factory=list)
    is_compressed: bool = False
    original_length: Optional[int] = None
    conversation_turn: int = 0


class TokenCounter:
    """Token counting utilities for different models"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "cl100k_base"
        self._encoding = None
        self._init_encoding()
    
    def _init_encoding(self):
        """Initialize tokenizer encoding"""
        try:
            # Map common model names to encodings
            encoding_map = {
                "qwen": "cl100k_base",
                "llama": "cl100k_base", 
                "gpt-4": "cl100k_base",
                "gpt-3.5": "cl100k_base",
                "claude": "cl100k_base"
            }
            
            encoding_name = "cl100k_base"  # Default
            for model_prefix, encoding in encoding_map.items():
                if model_prefix in self.model_name.lower():
                    encoding_name = encoding
                    break
            
            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to initialize tokenizer: {e}, using character approximation")
            self._encoding = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self._encoding:
            try:
                return len(self._encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token encoding failed: {e}, using character approximation")
        
        # Fallback: rough approximation (4 characters = 1 token)
        return len(text) // 4
    
    def count_message_tokens(self, message: LLMMessage) -> int:
        """Count tokens in a message including role overhead"""
        base_tokens = self.count_tokens(message.content)
        role_overhead = len(message.role) // 4 + 1  # Role name overhead
        return base_tokens + role_overhead


class MessageCompressor:
    """Message compression utilities for conversation optimization"""
    
    @staticmethod
    def compress_message(message: LLMMessage, target_length: int = 500) -> LLMMessage:
        """Compress a message while preserving key information"""
        content = message.content
        
        if len(content) <= target_length:
            return message
        
        # Extract key sentences (first and last sentences, plus any with keywords)
        sentences = content.split('. ')
        if len(sentences) <= 3:
            # If very few sentences, just truncate
            compressed_content = content[:target_length] + "..."
        else:
            key_sentences = []
            
            # Always keep first sentence
            key_sentences.append(sentences[0])
            
            # Look for sentences with important keywords
            important_keywords = ["iam", "security", "risk", "critical", "error", "fail"]
            for sentence in sentences[1:-1]:
                if any(keyword in sentence.lower() for keyword in important_keywords):
                    key_sentences.append(sentence)
                    if len('. '.join(key_sentences)) > target_length * 0.8:
                        break
            
            # Always try to keep last sentence if space allows
            combined = '. '.join(key_sentences)
            if len(combined) + len(sentences[-1]) <= target_length:
                key_sentences.append(sentences[-1])
            
            compressed_content = '. '.join(key_sentences)
            if len(compressed_content) > target_length:
                compressed_content = compressed_content[:target_length] + "..."
        
        # Create compressed message with updated metadata
        compressed_message = LLMMessage(
            role=message.role,
            content=compressed_content,
            metadata={
                **(message.metadata or {}),
                "is_compressed": True,
                "original_length": len(content),
                "compression_ratio": len(compressed_content) / len(content)
            }
        )
        
        return compressed_message
    
    @staticmethod
    def summarize_conversation_segment(messages: List[LLMMessage]) -> LLMMessage:
        """Summarize a segment of conversation into a single message"""
        if not messages:
            return LLMMessage(role="system", content="")
        
        # Extract key points from the conversation segment
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        summary_parts = []
        
        if user_messages:
            user_topics = []
            for msg in user_messages[-3:]:  # Last 3 user messages
                # Extract key topics (simplified)
                content_lower = msg.content.lower()
                if "iam" in content_lower:
                    user_topics.append("IAM changes")
                elif "risk" in content_lower:
                    user_topics.append("risk assessment")
                elif "stack" in content_lower:
                    user_topics.append("stack analysis")
                else:
                    # Extract first few words as topic
                    words = msg.content.split()[:5]
                    user_topics.append(" ".join(words))
            
            if user_topics:
                summary_parts.append(f"User asked about: {', '.join(set(user_topics))}")
        
        if assistant_messages:
            # Extract key findings from assistant responses
            key_findings = []
            for msg in assistant_messages[-2:]:  # Last 2 assistant messages
                lines = msg.content.split('\n')
                for line in lines:
                    if any(indicator in line.lower() for indicator in ["risk:", "finding:", "important:", "critical:"]):
                        key_findings.append(line.strip())
                        if len(key_findings) >= 3:
                            break
            
            if key_findings:
                summary_parts.append(f"Key findings: {'; '.join(key_findings[:3])}")
        
        summary_content = " | ".join(summary_parts) if summary_parts else "Previous conversation segment"
        
        return LLMMessage(
            role="system",
            content=f"[CONVERSATION SUMMARY]: {summary_content}",
            metadata={
                "is_summary": True,
                "summarized_messages": len(messages),
                "timestamp": datetime.now().isoformat()
            }
        )


class ConversationManager:
    """
    Modern conversation manager implementing AI best practices
    
    Features:
    - Structured message history with role-based conversation flow
    - Token-aware context management with intelligent truncation  
    - Configurable retention strategies for resource efficiency
    - Message compression and semantic importance scoring
    - Async processing for non-blocking state management
    """
    
    def __init__(self, config: ConversationConfig, llm_config: Optional[LLMConfig] = None):
        self.config = config
        self.llm_config = llm_config
        
        # Core conversation state
        self.messages: List[LLMMessage] = []
        self.message_metadata: List[MessageMetadata] = []
        self.conversation_turn = 0
        
        # Token management
        model_name = llm_config.model if llm_config else "qwen"
        self.token_counter = TokenCounter(model_name) if config.enable_token_counting else None
        self.compressor = MessageCompressor() if config.enable_compression else None
        
        # Statistics
        self.stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "compressions_performed": 0,
            "truncations_performed": 0,
            "important_messages_preserved": 0
        }
        
        logger.info(f"ConversationManager initialized with {config.retention_strategy} strategy")
    
    async def add_message(self, message: LLMMessage) -> None:
        """Add a message to conversation history with intelligent management"""
        if not self.config.enabled:
            return
        
        # Create enhanced metadata
        metadata = MessageMetadata(
            timestamp=datetime.now(),
            importance=self._assess_message_importance(message),
            token_count=self._count_message_tokens(message),
            contains_keywords=self._extract_keywords(message),
            conversation_turn=self.conversation_turn
        )
        
        # Add to conversation
        self.messages.append(message)
        self.message_metadata.append(metadata)
        
        # Update statistics
        self.stats["total_messages"] += 1
        self.stats["total_tokens"] += metadata.token_count
        
        # Increment turn counter for user messages
        if message.role == "user":
            self.conversation_turn += 1
        
        # Apply retention policy
        await self._apply_retention_policy()
        
        logger.debug(f"Added {message.role} message ({metadata.token_count} tokens, {metadata.importance} importance)")
    
    async def get_conversation_context(self, max_tokens: Optional[int] = None) -> List[LLMMessage]:
        """Get conversation context optimized for LLM consumption"""
        if not self.config.enabled or not self.messages:
            return []
        
        max_tokens = max_tokens or self.config.max_history_tokens
        
        # Start with recent messages and work backwards
        context_messages = []
        current_tokens = 0
        
        # Always include system messages if configured
        system_messages = []
        if self.config.include_system_messages:
            system_messages = [
                msg for i, msg in enumerate(self.messages) 
                if msg.role == "system" and not self.message_metadata[i].is_compressed
            ]
            for msg in system_messages:
                msg_tokens = self._count_message_tokens(msg)
                if current_tokens + msg_tokens <= max_tokens:
                    context_messages.append(msg)
                    current_tokens += msg_tokens
        
        # Add recent messages in reverse order (newest first for token budgeting)
        for i in range(len(self.messages) - 1, -1, -1):
            message = self.messages[i]
            metadata = self.message_metadata[i]
            
            # Skip system messages if already included
            if message.role == "system" and self.config.include_system_messages:
                continue
            
            msg_tokens = metadata.token_count
            if current_tokens + msg_tokens <= max_tokens:
                context_messages.insert(0, message)  # Insert at beginning to maintain order
                current_tokens += msg_tokens
            else:
                # Try compression if enabled
                if self.compressor and not metadata.is_compressed:
                    compressed_msg = self.compressor.compress_message(message)
                    compressed_tokens = self._count_message_tokens(compressed_msg)
                    
                    if current_tokens + compressed_tokens <= max_tokens:
                        context_messages.insert(0, compressed_msg)
                        current_tokens += compressed_tokens
                        self.stats["compressions_performed"] += 1
                        logger.debug(f"Compressed message from {msg_tokens} to {compressed_tokens} tokens")
                        continue
                
                # No more space available
                break
        
        logger.debug(f"Conversation context: {len(context_messages)} messages, {current_tokens} tokens")
        return context_messages
    
    async def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.messages.clear()
        self.message_metadata.clear()
        self.conversation_turn = 0
        
        # Reset statistics
        self.stats = {
            "total_messages": 0,
            "total_tokens": 0,
            "compressions_performed": 0,
            "truncations_performed": 0,
            "important_messages_preserved": 0
        }
        
        logger.info("Conversation history cleared")
    
    async def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation state"""
        total_tokens = sum(meta.token_count for meta in self.message_metadata)
        
        importance_distribution = {}
        for meta in self.message_metadata:
            importance_distribution[meta.importance] = importance_distribution.get(meta.importance, 0) + 1
        
        keyword_frequency = {}
        for meta in self.message_metadata:
            for keyword in meta.contains_keywords:
                keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
        
        return {
            "total_messages": len(self.messages),
            "total_tokens": total_tokens,
            "conversation_turns": self.conversation_turn,
            "average_tokens_per_message": total_tokens / len(self.messages) if self.messages else 0,
            "importance_distribution": importance_distribution,
            "keyword_frequency": keyword_frequency,
            "retention_strategy": self.config.retention_strategy,
            "statistics": self.stats.copy()
        }
    
    def _assess_message_importance(self, message: LLMMessage) -> MessageImportance:
        """Assess the importance of a message for retention priority"""
        content_lower = message.content.lower()
        
        # Critical messages
        if any(keyword in content_lower for keyword in ["critical", "error", "fail", "urgent"]):
            return MessageImportance.CRITICAL
        
        # High importance messages
        if any(keyword in content_lower for keyword in self.config.important_keywords):
            return MessageImportance.HIGH
        
        # Medium importance for longer messages or questions
        if len(message.content) > 200 or message.content.endswith('?'):
            return MessageImportance.MEDIUM
        
        return MessageImportance.LOW
    
    def _extract_keywords(self, message: LLMMessage) -> List[str]:
        """Extract important keywords from a message"""
        content_lower = message.content.lower()
        found_keywords = []
        
        all_keywords = self.config.important_keywords + [
            "risk", "security", "critical", "high", "medium", "low",
            "stack", "resource", "change", "delete", "add", "modify"
        ]
        
        for keyword in all_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _count_message_tokens(self, message: LLMMessage) -> int:
        """Count tokens in a message"""
        if self.token_counter:
            return self.token_counter.count_message_tokens(message)
        else:
            # Fallback approximation
            return len(message.content) // 4
    
    async def _apply_retention_policy(self) -> None:
        """Apply retention policy to manage conversation size"""
        if not self.messages:
            return
        
        # Check if we need to apply retention
        total_tokens = sum(meta.token_count for meta in self.message_metadata)
        
        should_apply_retention = (
            len(self.messages) > self.config.max_history_messages or
            total_tokens > self.config.max_history_tokens
        )
        
        if not should_apply_retention:
            return
        
        if self.config.retention_strategy == RetentionStrategy.SLIDING_WINDOW:
            await self._apply_sliding_window_retention()
        elif self.config.retention_strategy == RetentionStrategy.SEMANTIC_COMPRESSION:
            await self._apply_semantic_compression_retention()
        elif self.config.retention_strategy == RetentionStrategy.FIXED:
            await self._apply_fixed_retention()
    
    async def _apply_sliding_window_retention(self) -> None:
        """Apply sliding window retention strategy"""
        target_messages = self.config.max_history_messages
        
        if len(self.messages) <= target_messages:
            return
        
        # Identify important messages to preserve
        important_indices = []
        for i, metadata in enumerate(self.message_metadata):
            if (metadata.importance in [MessageImportance.CRITICAL, MessageImportance.HIGH] or
                len(metadata.contains_keywords) > 0):
                important_indices.append(i)
        
        # Keep the most recent messages and important messages
        keep_indices = set()
        
        # Always keep last N messages
        recent_count = min(target_messages // 2, len(self.messages))
        keep_indices.update(range(len(self.messages) - recent_count, len(self.messages)))
        
        # Keep important messages up to the limit
        important_to_keep = self.config.preserve_last_n_important
        recent_important = sorted(important_indices, reverse=True)[:important_to_keep]
        keep_indices.update(recent_important)
        
        # Ensure we don't exceed target
        keep_indices = sorted(list(keep_indices))[-target_messages:]
        
        # Update arrays
        self.messages = [self.messages[i] for i in keep_indices]
        self.message_metadata = [self.message_metadata[i] for i in keep_indices]
        
        removed_count = len(self.message_metadata) - len(keep_indices)
        if removed_count > 0:
            self.stats["truncations_performed"] += 1
            self.stats["important_messages_preserved"] += len([i for i in keep_indices if i in important_indices])
            logger.debug(f"Sliding window retention: removed {removed_count} messages, kept {len(keep_indices)}")
    
    async def _apply_semantic_compression_retention(self) -> None:
        """Apply semantic compression retention strategy"""
        if not self.compressor:
            # Fallback to sliding window if compression not available
            await self._apply_sliding_window_retention()
            return
        
        # Identify conversation segments to compress
        segments = self._identify_compression_segments()
        
        for start_idx, end_idx in segments:
            if end_idx - start_idx > 2:  # Only compress segments with multiple messages
                segment_messages = self.messages[start_idx:end_idx]
                summary_message = self.compressor.summarize_conversation_segment(segment_messages)
                
                # Replace segment with summary
                self.messages[start_idx:end_idx] = [summary_message]
                
                # Update metadata
                summary_metadata = MessageMetadata(
                    timestamp=datetime.now(),
                    importance=MessageImportance.MEDIUM,
                    token_count=self._count_message_tokens(summary_message),
                    contains_keywords=[],
                    is_compressed=True,
                    conversation_turn=self.message_metadata[start_idx].conversation_turn
                )
                
                self.message_metadata[start_idx:end_idx] = [summary_metadata]
                
                self.stats["compressions_performed"] += 1
                logger.debug(f"Compressed conversation segment: {end_idx - start_idx} messages → 1 summary")
    
    async def _apply_fixed_retention(self) -> None:
        """Apply fixed retention strategy (simple truncation)"""
        target_messages = self.config.max_history_messages
        
        if len(self.messages) > target_messages:
            # Remove oldest messages
            remove_count = len(self.messages) - target_messages
            self.messages = self.messages[remove_count:]
            self.message_metadata = self.message_metadata[remove_count:]
            
            self.stats["truncations_performed"] += 1
            logger.debug(f"Fixed retention: removed {remove_count} oldest messages")
    
    def _identify_compression_segments(self) -> List[Tuple[int, int]]:
        """Identify conversation segments that can be compressed"""
        segments = []
        current_start = 0
        
        for i in range(1, len(self.messages)):
            # Look for natural break points (time gaps, topic changes)
            time_gap = (self.message_metadata[i].timestamp - 
                       self.message_metadata[i-1].timestamp).total_seconds()
            
            # If there's a significant time gap (>5 minutes) or we hit the compression threshold
            if (time_gap > 300 or  # 5 minutes
                i - current_start >= self.config.max_history_messages * self.config.compression_threshold):
                
                if i - current_start > 2:  # Only compress if segment has multiple messages
                    segments.append((current_start, i))
                current_start = i
        
        return segments