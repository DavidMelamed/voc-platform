"""
Text chunking utilities for the Tagger Agent.

This module provides functionality for splitting text into smaller chunks
with configurable overlap for processing and embedding.
"""

import re
import logging
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextChunker:
    """
    Utility for splitting text into chunks with overlap.
    
    This helps with processing long documents by breaking them into
    smaller pieces that can be processed and embedded separately.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in tokens (approximate)
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Validate parameters
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
            
        logger.info(f"Initialized TextChunker with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        
    async def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
            
        # Approximately convert chunk size and overlap from tokens to characters
        # This is a rough approximation, assuming average token length of 4-5 characters
        avg_token_length = 4.5
        char_chunk_size = int(self.chunk_size * avg_token_length)
        char_overlap = int(self.chunk_overlap * avg_token_length)
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        # Group paragraphs into chunks
        return self._create_chunks_from_paragraphs(paragraphs, char_chunk_size, char_overlap)
        
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines (common paragraph separator)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs and strip whitespace
        return [p.strip() for p in paragraphs if p.strip()]
        
    def _create_chunks_from_paragraphs(
        self, 
        paragraphs: List[str], 
        char_chunk_size: int, 
        char_overlap: int
    ) -> List[str]:
        """
        Group paragraphs into chunks.
        
        Args:
            paragraphs: List of paragraphs to group
            char_chunk_size: Maximum chunk size in characters
            char_overlap: Overlap size in characters
            
        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # If adding this paragraph would exceed the chunk size,
            # and we already have content in the current chunk,
            # then finalize the current chunk and start a new one
            if current_size + paragraph_size > char_chunk_size and current_chunk:
                # Join the current chunk paragraphs and add to chunks
                chunks.append('\n\n'.join(current_chunk))
                
                # Start a new chunk with overlap
                # Keep paragraphs that fit within the overlap size
                overlap_size = 0
                overlap_paragraphs = []
                
                for p in reversed(current_chunk):
                    p_size = len(p)
                    if overlap_size + p_size <= char_overlap:
                        overlap_paragraphs.insert(0, p)
                        overlap_size += p_size
                    else:
                        break
                        
                current_chunk = overlap_paragraphs
                current_size = overlap_size
                
            # Add the paragraph to the current chunk
            current_chunk.append(paragraph)
            current_size += paragraph_size
            
            # If a single paragraph is larger than the chunk size,
            # we need to split it further
            if paragraph_size > char_chunk_size:
                # First, add the current chunk (which now has this large paragraph)
                chunks.append('\n\n'.join(current_chunk))
                
                # Then split the large paragraph into smaller chunks
                # and add them as separate chunks
                sentences = self._split_into_sentences(paragraph)
                sentence_chunks = self._create_chunks_from_sentences(
                    sentences, char_chunk_size, char_overlap
                )
                
                for sc in sentence_chunks[1:]:  # Skip the first one as it's already added
                    chunks.append(sc)
                    
                # Reset the current chunk
                current_chunk = []
                current_size = 0
                
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
        return chunks
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # This is a simplified sentence splitter
        # In a production environment, you might want to use a more sophisticated approach
        # such as NLTK's sentence tokenizer
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        
        # Filter out empty sentences and strip whitespace
        return [s.strip() for s in sentences if s.strip()]
        
    def _create_chunks_from_sentences(
        self, 
        sentences: List[str], 
        char_chunk_size: int, 
        char_overlap: int
    ) -> List[str]:
        """
        Group sentences into chunks.
        
        Args:
            sentences: List of sentences to group
            char_chunk_size: Maximum chunk size in characters
            char_overlap: Overlap size in characters
            
        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed the chunk size,
            # and we already have content in the current chunk,
            # then finalize the current chunk and start a new one
            if current_size + sentence_size > char_chunk_size and current_chunk:
                # Join the current chunk sentences and add to chunks
                chunks.append(' '.join(current_chunk))
                
                # Start a new chunk with overlap
                # Keep sentences that fit within the overlap size
                overlap_size = 0
                overlap_sentences = []
                
                for s in reversed(current_chunk):
                    s_size = len(s)
                    if overlap_size + s_size <= char_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += s_size
                    else:
                        break
                        
                current_chunk = overlap_sentences
                current_size = overlap_size
                
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
            
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
