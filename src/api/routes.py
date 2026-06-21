"""
API routes for document intelligence agent
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os

from ..agent import (
    DocumentParser,
    QAEngine,
    DocumentSummarizer,
    EntityExtractor,
    DocumentComparator
)

router = APIRouter()

# Initialize agents
parser = DocumentParser()
qa_engine = QAEngine()
summarizer = DocumentSummarizer()
entity_extractor = EntityExtractor()
comparator = DocumentComparator()


# Request/Response Models
class QuestionRequest(BaseModel):
    document_id: str
    question: str
    num_relevant_chunks: Optional[int] = 3


class SummaryRequest(BaseModel):
    content: str
    max_length: Optional[int] = 150
    style: Optional[str] = "paragraph"  # paragraph or bullets


class CompareRequest(BaseModel):
    doc1_content: str
    doc2_content: str
    doc1_name: Optional[str] = "Document 1"
    doc2_name: Optional[str] = "Document 2"


# Routes
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    index_for_qa: bool = Form(default=True)
):
    """
    Upload and parse a document

    Supports: PDF, Word, Excel, PowerPoint, Text, CSV, Markdown
    """
    try:
        # Get file extension
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower().lstrip('.')

        # Read file content
        content = await file.read()

        # Parse document
        parsed = parser.parse_document(
            file_content=content,
            file_extension=ext
        )

        if 'error' in parsed:
            raise HTTPException(status_code=400, detail=parsed['error'])

        # Index for Q&A if requested
        if index_for_qa and 'content' in parsed:
            index_result = qa_engine.index_document(
                document_content=parsed['content'],
                document_id=filename,
                metadata={"filename": filename, "format": ext}
            )
            parsed['indexed'] = index_result

        return {
            "filename": filename,
            "format": ext,
            "parsed": parsed,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_document_content(
    content: str,
    format: str = "txt"
):
    """Parse document from text content"""
    try:
        parsed = parser.parse_document(
            file_content=content.encode('utf-8'),
            file_extension=format
        )

        if 'error' in parsed:
            raise HTTPException(status_code=400, detail=parsed['error'])

        return parsed

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qa")
async def ask_question(request: QuestionRequest):
    """Ask a question about an indexed document"""
    try:
        result = qa_engine.ask_question(
            question=request.question,
            document_id=request.document_id,
            num_relevant_chunks=request.num_relevant_chunks
        )

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_document(request: SummaryRequest):
    """Generate document summary"""
    try:
        summary = summarizer.summarize(
            content=request.content,
            max_length=request.max_length,
            style=request.style
        )

        if 'error' in summary:
            raise HTTPException(status_code=400, detail=summary['error'])

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-entities")
async def extract_entities(content: str):
    """Extract entities from document"""
    try:
        entities = entity_extractor.extract_entities(content)

        if 'error' in entities:
            raise HTTPException(status_code=400, detail=entities['error'])

        return entities

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_documents(request: CompareRequest):
    """Compare two documents"""
    try:
        comparison = comparator.compare_documents(
            doc1_content=request.doc1_content,
            doc2_content=request.doc2_content,
            doc1_name=request.doc1_name,
            doc2_name=request.doc2_name
        )

        if 'error' in comparison:
            raise HTTPException(status_code=400, detail=comparison['error'])

        return comparison

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/key-points")
async def extract_key_points(
    content: str,
    num_points: int = 5
):
    """Extract key points from document"""
    try:
        result = summarizer.extract_key_points(content, num_points)

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/abstract")
async def generate_abstract(
    content: str,
    max_words: int = 250
):
    """Generate academic-style abstract"""
    try:
        abstract = summarizer.generate_abstract(content, max_words)

        if 'error' in abstract:
            raise HTTPException(status_code=400, detail=abstract['error'])

        return abstract

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    query: str,
    max_results: int = 5
):
    """Search across indexed documents"""
    try:
        results = qa_engine.search_documents(query, max_results)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    return {
        "formats": parser.get_supported_formats(),
        "count": len(parser.get_supported_formats())
    }


@router.post("/entity-frequency")
async def get_entity_frequency(content: str):
    """Get frequency count of entities"""
    try:
        frequencies = entity_extractor.get_entity_frequency(content)
        return frequencies

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-summary")
async def compare_summary_styles(content: str):
    """Generate multiple summary styles for comparison"""
    try:
        summaries = summarizer.compare_summaries(content)

        if 'error' in summaries:
            raise HTTPException(status_code=400, detail=summaries['error'])

        return summaries

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
