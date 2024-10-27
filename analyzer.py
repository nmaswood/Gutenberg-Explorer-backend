from typing import Dict, List, Optional , Generator
from pydantic import BaseModel
import json
import os
from typing import Dict
from langchain_together import ChatTogether

class BookChunker:
    def __init__(self, max_chunk_tokens: int = 3000):
        self.max_chunk_tokens = max_chunk_tokens
        
    def estimate_tokens(self, text: str) -> int:
        
        return len(text) // 3
        
    def split_into_chunks(self, text: str) -> List[str]:
        # Split into smaller, more manageable chunks
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_tokens = self.estimate_tokens(word + ' ')
            
            if current_length + word_tokens > self.max_chunk_tokens:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

class BookAnalyzer:
    def __init__(self, chat_instance):
        self.chat = chat_instance
        self.chunker = BookChunker()
        # Simplified prompt to reduce token usage
        self.analysis_prompt_template = """
        Analyze this book segment focusing on:
        {content}
        
        Provide:
        1. Key events
        2. Characters present
        3. Important themes
        4. Notable developments
        """
        
        self.summary_prompt_template = """
        Synthesize these segment analyses into a complete book analysis:
        {previous_analyses}
        
        Provide:
        1. Main characters and roles
        2. Character relationships
        3. Plot summary
        4. Key themes
        5. Writing style
        6. Overall message
        """

    def create_analysis_prompt(self, content: str) -> str:
        return self.analysis_prompt_template.format(content=content)
        
    def create_summary_prompt(self, analyses: List[str]) -> str:
        # Take only essential information from each analysis
        summarized_analyses = []
        for i, analysis in enumerate(analyses, 1):
            # Limit each analysis summary to reduce tokens
            summary = f"Section {i}: {analysis[:1000]}..."
            summarized_analyses.append(summary)
            
        combined_analyses = "\n---\n".join(summarized_analyses[-3:])  # Only keep last 3 sections
        return self.summary_prompt_template.format(previous_analyses=combined_analyses)

    def get_llm_analysis(self, content: str) -> str:
        prompt = self.create_analysis_prompt(content)
        # Add token count debugging
        estimated_tokens = self.chunker.estimate_tokens(prompt)
        if estimated_tokens > 4000: 
            raise Exception(f"Prompt too long: estimated {estimated_tokens} tokens")
            
        response = ""
        for message_chunk in self.chat.stream(prompt):
            response += message_chunk.content
        return response
        
    def analyze_content(self, content: str):
        try:
            print(f"Total content length: {len(content)} characters")
            chunks = self.chunker.split_into_chunks(content)
            print(f"Split into {len(chunks)} chunks")
            
            chunk_analyses = []
            for i, chunk in enumerate(chunks, 1):
                print(f"Analyzing chunk {i}/{len(chunks)} - {len(chunk)} characters")
                try:
                    analysis = self.get_llm_analysis(chunk)
                    chunk_analyses.append(analysis)
                    yield analysis  # Yield each analysis result immediately
                except Exception as chunk_error:
                    print(f"Warning: Chunk {i} analysis failed: {str(chunk_error)}")
                    continue
            
            # Optionally yield a summary if needed at the end
            if chunk_analyses:
                final_prompt = self.create_summary_prompt(chunk_analyses)
                final_analysis = ""
                for message_chunk in self.chat.stream(final_prompt):
                    final_analysis += message_chunk.content
                yield final_analysis  # Yield the final summary
                
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")