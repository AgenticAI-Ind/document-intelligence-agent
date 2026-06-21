"""
Document summarization with AI
"""

import logging
from typing import Dict, List, Optional
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """Automatic document summarization"""

    def __init__(self, model_name: str = "llama3.2"):
        """Initialize summarizer"""
        self.llm = Ollama(model=model_name)

        self.summary_prompt = PromptTemplate(
            input_variables=["content", "max_length"],
            template="""Summarize the following document in {max_length} words or less.

Document:
{content}

Provide a clear, concise summary that captures the main points and key information.

Summary:"""
        )

        self.bullet_prompt = PromptTemplate(
            input_variables=["content", "num_points"],
            template="""Create {num_points} bullet point summary of this document:

{content}

Format as:
• Point 1
• Point 2
• Point 3

Bullet Summary:"""
        )

    def summarize(
        self,
        content: str,
        max_length: int = 150,
        style: str = "paragraph"
    ) -> Dict:
        """
        Generate document summary

        Args:
            content: Document content to summarize
            max_length: Maximum length in words
            style: 'paragraph' or 'bullets'

        Returns:
            Dict with summary and metadata
        """
        try:
            if style == "bullets":
                num_points = max(3, max_length // 25)  # ~25 words per bullet
                return self._summarize_bullets(content, num_points)
            else:
                return self._summarize_paragraph(content, max_length)

        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                "summary": "Error generating summary",
                "error": str(e)
            }

    def _summarize_paragraph(self, content: str, max_length: int) -> Dict:
        """Generate paragraph summary"""
        # Truncate if too long for context
        truncated_content = content[:10000]

        prompt = self.summary_prompt.format(
            content=truncated_content,
            max_length=max_length
        )

        summary = self.llm.invoke(prompt)

        return {
            "summary": summary.strip(),
            "style": "paragraph",
            "word_count": len(summary.split()),
            "original_length": len(content),
            "compression_ratio": len(content) / len(summary)
        }

    def _summarize_bullets(self, content: str, num_points: int) -> Dict:
        """Generate bullet point summary"""
        truncated_content = content[:10000]

        prompt = self.bullet_prompt.format(
            content=truncated_content,
            num_points=num_points
        )

        summary = self.llm.invoke(prompt)

        # Parse bullets
        bullets = self._parse_bullets(summary)

        return {
            "summary": "\n".join(bullets),
            "bullets": bullets,
            "style": "bullets",
            "bullet_count": len(bullets),
            "original_length": len(content)
        }

    def _parse_bullets(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        lines = text.strip().split('\n')
        bullets = []

        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or
                        line.startswith('*') or line[0].isdigit()):
                bullet = line.lstrip('•-*0123456789. ').strip()
                if bullet:
                    bullets.append(bullet)

        return bullets

    def extract_key_points(self, content: str, num_points: int = 5) -> Dict:
        """
        Extract key points from document

        Args:
            content: Document content
            num_points: Number of key points to extract

        Returns:
            Dict with key points
        """
        try:
            prompt = f"""Extract the {num_points} most important key points from this document:

{content[:8000]}

List them as numbered points:
1. [First key point]
2. [Second key point]
etc.

Key Points:"""

            response = self.llm.invoke(prompt)

            # Parse numbered points
            points = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    point = line.split('.', 1)[1].strip() if '.' in line else line
                    points.append(point)

            return {
                "key_points": points,
                "count": len(points)
            }

        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return {"key_points": [], "error": str(e)}

    def generate_abstract(self, content: str, max_words: int = 250) -> Dict:
        """
        Generate academic-style abstract

        Args:
            content: Document content
            max_words: Maximum abstract length

        Returns:
            Dict with abstract
        """
        try:
            prompt = f"""Write a professional abstract (max {max_words} words) for this document:

{content[:8000]}

The abstract should include:
1. Purpose/objective
2. Methods/approach
3. Key findings
4. Conclusions

Abstract:"""

            abstract = self.llm.invoke(prompt)

            return {
                "abstract": abstract.strip(),
                "word_count": len(abstract.split()),
                "style": "academic"
            }

        except Exception as e:
            logger.error(f"Error generating abstract: {e}")
            return {"abstract": "", "error": str(e)}

    def summarize_by_sections(
        self,
        sections: List[Dict],
        summary_length: int = 50
    ) -> Dict:
        """
        Summarize document section by section

        Args:
            sections: List of dicts with 'title' and 'content'
            summary_length: Words per section summary

        Returns:
            Dict with section summaries
        """
        section_summaries = []

        for section in sections:
            title = section.get('title', 'Untitled Section')
            content = section.get('content', '')

            if not content:
                continue

            try:
                summary = self.summarize(
                    content,
                    max_length=summary_length,
                    style="paragraph"
                )

                section_summaries.append({
                    "title": title,
                    "summary": summary['summary'],
                    "original_length": len(content)
                })

            except Exception as e:
                logger.error(f"Error summarizing section '{title}': {e}")
                section_summaries.append({
                    "title": title,
                    "summary": "Error generating summary",
                    "error": str(e)
                })

        return {
            "section_summaries": section_summaries,
            "section_count": len(section_summaries)
        }

    def generate_executive_summary(
        self,
        content: str,
        target_audience: str = "executives"
    ) -> Dict:
        """
        Generate executive summary tailored to audience

        Args:
            content: Document content
            target_audience: Target audience type

        Returns:
            Dict with executive summary
        """
        try:
            prompt = f"""Create an executive summary for {target_audience}:

{content[:8000]}

Focus on:
- Key business insights
- Strategic implications
- Action items
- ROI/impact

Keep it concise (200 words max) and actionable.

Executive Summary:"""

            summary = self.llm.invoke(prompt)

            return {
                "executive_summary": summary.strip(),
                "target_audience": target_audience,
                "word_count": len(summary.split())
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {"executive_summary": "", "error": str(e)}

    def compare_summaries(
        self,
        content: str
    ) -> Dict:
        """
        Generate multiple summary styles for comparison

        Args:
            content: Document content

        Returns:
            Dict with different summary styles
        """
        try:
            paragraph = self.summarize(content, max_length=150, style="paragraph")
            bullets = self.summarize(content, max_length=150, style="bullets")
            key_points = self.extract_key_points(content, num_points=5)
            abstract = self.generate_abstract(content, max_words=200)

            return {
                "paragraph": paragraph['summary'],
                "bullets": bullets.get('bullets', []),
                "key_points": key_points['key_points'],
                "abstract": abstract['abstract']
            }

        except Exception as e:
            logger.error(f"Error comparing summaries: {e}")
            return {"error": str(e)}
