"""
Content chunking strategies for diff files.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkType(str, Enum):
    """Types of content chunks."""
    STACK_HEADER = "stack_header"
    IAM_SECTION = "iam_section"
    RESOURCES_SECTION = "resources_section"
    TEMPLATE_SECTION = "template_section"
    RESOURCE_CHANGE = "resource_change"
    IAM_STATEMENT = "iam_statement"
    FULL_DIFF = "full_diff"


@dataclass
class ContentChunk:
    """A chunk of diff content with metadata."""
    content: str
    chunk_type: ChunkType
    metadata: Dict[str, Any]
    start_line: int
    end_line: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for storage."""
        return {
            "content": self.content,
            "chunk_type": self.chunk_type.value,
            "metadata": self.metadata,
            "start_line": self.start_line,
            "end_line": self.end_line
        }


class DiffChunker:
    """Chunks diff file content into logical sections for embedding."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize diff chunker.
        
        Args:
            config: Chunking configuration
        """
        self.config = config
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 200)
        
        # Patterns for detecting sections
        self.patterns = {
            "stack_header": re.compile(r"^Stack\s+(.+?)\s*$", re.IGNORECASE),
            "iam_section": re.compile(r"^\s*\[\+\]\s*AWS::IAM::", re.IGNORECASE),
            "iam_statement_table": re.compile(r"^IAM Statement Changes\s*$", re.IGNORECASE),
            "resource_section": re.compile(r"^\s*Resources\s*$", re.IGNORECASE),
            "template_section": re.compile(r"^\s*Template\s*$", re.IGNORECASE),
            "resource_change": re.compile(r"^\s*\[([+\-~])\]\s*(.+?)$"),
            "change_line": re.compile(r"^\s*([+\-~])\s*(.+)$"),
            "table_border": re.compile(r"^[┌┬┐├┼┤└┴┘│─]+$")
        }
        
    def chunk_diff_file(
        self, 
        content: str, 
        filename: str,
        stack_name: Optional[str] = None,
        account_id: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[ContentChunk]:
        """Chunk a diff file into logical sections.
        
        Args:
            content: Full diff file content
            filename: Name of the diff file
            stack_name: Stack name (if known)
            account_id: Account ID (if known)
            region: Region (if known)
            
        Returns:
            List of content chunks
        """
        lines = content.split('\n')
        chunks = []
        
        # Extract metadata from filename if not provided
        if not stack_name:
            stack_name = self._extract_stack_name(filename)
        if not account_id:
            account_id = self._extract_account_id(filename)
        if not region:
            region = self._extract_region(filename)
            
        base_metadata = {
            "filename": filename,
            "stack_name": stack_name,
            "account_id": account_id,
            "region": region,
            "total_lines": len(lines)
        }
        
        # Create full diff chunk for complete context
        chunks.append(ContentChunk(
            content=content,
            chunk_type=ChunkType.FULL_DIFF,
            metadata={**base_metadata, "description": "Complete diff file"},
            start_line=1,
            end_line=len(lines)
        ))
        
        # Parse into logical sections
        sections = self._parse_sections(lines)
        
        # Extract IAM statement tables as complete chunks
        iam_chunks = self._extract_iam_statement_chunks(content, base_metadata)
        chunks.extend(iam_chunks)
        
        for section in sections:
            section_chunks = self._chunk_section(
                section, 
                base_metadata
            )
            chunks.extend(section_chunks)
            
        # Create overlapping chunks for better context
        overlap_chunks = self._create_overlap_chunks(content, base_metadata)
        chunks.extend(overlap_chunks)
        
        logger.info(f"Created {len(chunks)} chunks for {filename}")
        return chunks
        
    def _parse_sections(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse diff content into logical sections."""
        sections = []
        current_section = None
        current_content = []
        current_type = None
        start_line = 0
        
        for i, line in enumerate(lines):
            # Detect section boundaries
            if self.patterns["stack_header"].match(line):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "type": ChunkType.STACK_HEADER,
                    "start_line": i + 1,
                    "content": [line],
                    "metadata": {"section": "header"}
                }
                current_type = ChunkType.STACK_HEADER
                
            elif self.patterns["template_section"].match(line):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "type": ChunkType.TEMPLATE_SECTION,
                    "start_line": i + 1,
                    "content": [line],
                    "metadata": {"section": "template"}
                }
                current_type = ChunkType.TEMPLATE_SECTION
                
            elif self.patterns["resource_section"].match(line):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "type": ChunkType.RESOURCES_SECTION,
                    "start_line": i + 1,
                    "content": [line],
                    "metadata": {"section": "resources"}
                }
                current_type = ChunkType.RESOURCES_SECTION
                
            elif self.patterns["iam_statement_table"].match(line):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "type": ChunkType.IAM_SECTION,
                    "start_line": i + 1,
                    "content": [line],
                    "metadata": {"section": "iam_statements"}
                }
                current_type = ChunkType.IAM_SECTION
                
            elif self.patterns["iam_section"].match(line):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "type": ChunkType.IAM_SECTION,
                    "start_line": i + 1,
                    "content": [line],
                    "metadata": {"section": "iam"}
                }
                current_type = ChunkType.IAM_SECTION
                
            else:
                # Add to current section
                if current_section:
                    current_section["content"].append(line)
                else:
                    # Start a generic section
                    current_section = {
                        "type": ChunkType.TEMPLATE_SECTION,
                        "start_line": i + 1,
                        "content": [line],
                        "metadata": {"section": "other"}
                    }
                    current_type = ChunkType.TEMPLATE_SECTION
        
        # Add final section
        if current_section:
            sections.append(current_section)
            
        # Set end lines
        for section in sections:
            section["end_line"] = section["start_line"] + len(section["content"]) - 1
            
        return sections
        
    def _chunk_section(
        self, 
        section: Dict[str, Any], 
        base_metadata: Dict[str, Any]
    ) -> List[ContentChunk]:
        """Chunk a section into smaller pieces if needed."""
        content_lines = section["content"]
        content = '\n'.join(content_lines)
        
        # If section is small enough, return as single chunk
        if len(content) <= self.chunk_size:
            return [ContentChunk(
                content=content,
                chunk_type=section["type"],
                metadata={
                    **base_metadata,
                    **section["metadata"],
                    "section_size": len(content)
                },
                start_line=section["start_line"],
                end_line=section["end_line"]
            )]
            
        # Split large sections
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start = section["start_line"]
        
        for i, line in enumerate(content_lines):
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_content = '\n'.join(current_chunk)
                chunks.append(ContentChunk(
                    content=chunk_content,
                    chunk_type=section["type"],
                    metadata={
                        **base_metadata,
                        **section["metadata"],
                        "chunk_index": len(chunks),
                        "section_size": len(content)
                    },
                    start_line=chunk_start,
                    end_line=chunk_start + len(current_chunk) - 1
                ))
                
                # Start new chunk with overlap
                overlap_lines = max(0, min(len(current_chunk), self.chunk_overlap // 50))
                current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                current_size = sum(len(line) + 1 for line in current_chunk)
                chunk_start = chunk_start + len(current_chunk) - overlap_lines
                
            current_chunk.append(line)
            current_size += line_size
            
        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(ContentChunk(
                content=chunk_content,
                chunk_type=section["type"],
                metadata={
                    **base_metadata,
                    **section["metadata"],
                    "chunk_index": len(chunks),
                    "section_size": len(content)
                },
                start_line=chunk_start,
                end_line=section["end_line"]
            ))
            
        return chunks
    
    def _extract_iam_statement_chunks(
        self, 
        content: str, 
        base_metadata: Dict[str, Any]
    ) -> List[ContentChunk]:
        """Extract IAM statement tables as complete, dedicated chunks."""
        chunks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for IAM Statement Changes header
            if self.patterns["iam_statement_table"].match(line):
                start_line = i + 1
                table_content = [line]
                i += 1
                
                # Collect the entire table including borders and content
                in_table = True
                while i < len(lines) and in_table:
                    current_line = lines[i]
                    
                    # Check if we're still in the table
                    if (self.patterns["table_border"].match(current_line) or
                        current_line.startswith('│') or 
                        current_line.startswith('├') or
                        current_line.startswith('└') or
                        current_line.startswith('┌') or
                        current_line.strip() == '' or
                        current_line.startswith('(NOTE:')):
                        table_content.append(current_line)
                        i += 1
                        
                        # Stop after NOTE section
                        if current_line.startswith('(NOTE:') and ')' in current_line:
                            break
                    else:
                        # We've reached the end of the table
                        in_table = False
                        break
                
                # Create IAM chunk with complete table
                iam_content = '\n'.join(table_content)
                chunks.append(ContentChunk(
                    content=iam_content,
                    chunk_type=ChunkType.IAM_SECTION,
                    metadata={
                        **base_metadata,
                        "section": "iam_statement_table",
                        "description": "Complete IAM statement changes table",
                        "is_table": True
                    },
                    start_line=start_line,
                    end_line=start_line + len(table_content) - 1
                ))
            else:
                i += 1
                
        return chunks
        
    def _create_overlap_chunks(
        self, 
        content: str, 
        base_metadata: Dict[str, Any]
    ) -> List[ContentChunk]:
        """Create overlapping chunks for better context preservation."""
        if len(content) <= self.chunk_size:
            return []
            
        chunks = []
        lines = content.split('\n')
        step_size = self.chunk_size - self.chunk_overlap
        
        for i in range(0, len(content), step_size):
            chunk_end = min(i + self.chunk_size, len(content))
            chunk_content = content[i:chunk_end]
            
            # Find line boundaries
            start_line = content[:i].count('\n') + 1
            end_line = content[:chunk_end].count('\n') + 1
            
            chunks.append(ContentChunk(
                content=chunk_content,
                chunk_type=ChunkType.TEMPLATE_SECTION,
                metadata={
                    **base_metadata,
                    "chunk_type": "overlap",
                    "chunk_index": len(chunks),
                    "overlap": True
                },
                start_line=start_line,
                end_line=end_line
            ))
            
        return chunks
        
    def _extract_stack_name(self, filename: str) -> Optional[str]:
        """Extract stack name from filename."""
        # Pattern: account-region-stackname-timestamp.diff
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 3:
            return '-'.join(parts[2:-1])  # Everything except account, region, timestamp
        return None
        
    def _extract_account_id(self, filename: str) -> Optional[str]:
        """Extract account ID from filename."""
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 1 and parts[0].isdigit():
            return parts[0]
        return None
        
    def _extract_region(self, filename: str) -> Optional[str]:
        """Extract region from filename."""
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 2:
            region_candidate = parts[1]
            # Basic validation for AWS region format
            if re.match(r'^[a-z]+-[a-z]+-\d+$', region_candidate):
                return region_candidate
        return None