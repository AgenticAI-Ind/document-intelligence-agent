"""
AI-powered Q&A engine for documents using RAG (Retrieval-Augmented Generation)
"""

import logging
from typing import Dict, List, Optional
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

logger = logging.getLogger(__name__)


class QAEngine:
    """Question-answering engine with RAG"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        embedding_model: str = "nomic-embed-text",
        persist_directory: str = "./data/chroma"
    ):
        """
        Initialize QA engine

        Args:
            model_name: Ollama model for generation
            embedding_model: Model for embeddings
            persist_directory: ChromaDB persistence directory
        """
        self.llm = Ollama(model=model_name)
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.persist_directory = persist_directory
        self.vector_store = None
        self.document_id = None

        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful assistant answering questions based on document content.

Context from document:
{context}

Question: {question}

Provide a clear, accurate answer based ONLY on the context provided. If the answer is not in the context, say "I cannot find this information in the document."

Answer:"""
        )

    def index_document(
        self,
        document_content: str,
        document_id: str,
        metadata: Optional[Dict] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict:
        """
        Index a document for Q&A

        Args:
            document_content: Full document text
            document_id: Unique identifier for the document
            metadata: Additional document metadata
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            Dict with indexing status and stats
        """
        try:
            # Split document into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
            )

            chunks = text_splitter.split_text(document_content)

            # Prepare metadata for each chunk
            metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)

            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = Chroma.from_texts(
                    texts=chunks,
                    embedding=self.embeddings,
                    metadatas=metadatas,
                    persist_directory=self.persist_directory,
                    collection_name=f"doc_{document_id}"
                )
            else:
                # Add to existing collection
                self.vector_store.add_texts(
                    texts=chunks,
                    metadatas=metadatas
                )

            self.document_id = document_id

            logger.info(f"Indexed document {document_id}: {len(chunks)} chunks")

            return {
                "status": "indexed",
                "document_id": document_id,
                "chunk_count": len(chunks),
                "total_chars": len(document_content),
                "avg_chunk_size": len(document_content) // len(chunks)
            }

        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def ask_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        num_relevant_chunks: int = 3
    ) -> Dict:
        """
        Ask a question about indexed documents

        Args:
            question: User's question
            document_id: Optional specific document to query
            num_relevant_chunks: Number of relevant chunks to retrieve

        Returns:
            Dict with answer, sources, and confidence
        """
        try:
            if self.vector_store is None:
                raise ValueError("No documents indexed. Call index_document() first.")

            # Retrieve relevant chunks
            if document_id:
                # Filter by document_id
                retriever = self.vector_store.as_retriever(
                    search_kwargs={
                        "k": num_relevant_chunks,
                        "filter": {"document_id": document_id}
                    }
                )
                docs = retriever.get_relevant_documents(question)
            else:
                # Search all documents
                docs = self.vector_store.similarity_search(
                    question,
                    k=num_relevant_chunks
                )

            if not docs:
                return {
                    "answer": "No relevant information found in the document.",
                    "sources": [],
                    "confidence": 0.0
                }

            # Combine context from retrieved chunks
            context = "\n\n".join([doc.page_content for doc in docs])

            # Generate answer
            prompt = self.qa_prompt.format(
                context=context[:3000],  # Limit context length
                question=question
            )

            answer = self.llm.invoke(prompt)

            # Extract sources
            sources = []
            for doc in docs:
                sources.append({
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "document_id": doc.metadata.get("document_id", "unknown"),
                    "preview": doc.page_content[:200] + "..."
                })

            logger.info(f"Answered question: {question[:50]}...")

            return {
                "answer": answer.strip(),
                "sources": sources,
                "source_count": len(sources),
                "confidence": self._estimate_confidence(answer, context)
            }

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "sources": [],
                "error": str(e)
            }

    def _estimate_confidence(self, answer: str, context: str) -> float:
        """
        Estimate confidence score based on answer characteristics

        Simple heuristic: if answer contains phrases like "I cannot find"
        or is very short, confidence is low
        """
        answer_lower = answer.lower()

        # Low confidence indicators
        if any(phrase in answer_lower for phrase in [
            "cannot find",
            "not in the document",
            "no information",
            "i don't know"
        ]):
            return 0.3

        # Very short answers might be uncertain
        if len(answer.split()) < 5:
            return 0.5

        # Length-based confidence
        if len(answer.split()) > 20:
            return 0.9

        return 0.7

    def multi_question_qa(
        self,
        questions: List[str],
        document_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Answer multiple questions in batch

        Args:
            questions: List of questions
            document_id: Optional specific document

        Returns:
            List of answer dicts
        """
        results = []
        for question in questions:
            result = self.ask_question(question, document_id)
            result['question'] = question
            results.append(result)

        return results

    def get_document_summary_qa(self, document_id: str) -> Dict:
        """
        Get a Q&A-style summary of the document

        Args:
            document_id: Document to summarize

        Returns:
            Dict with common questions answered
        """
        common_questions = [
            "What is this document about?",
            "What are the main points or key takeaways?",
            "Who is the target audience?",
            "What is the conclusion or recommendation?"
        ]

        results = {}
        for question in common_questions:
            answer = self.ask_question(question, document_id)
            results[question] = answer['answer']

        return {
            "document_id": document_id,
            "summary_qa": results
        }

    def search_documents(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search across all indexed documents

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of matching document chunks
        """
        try:
            if self.vector_store is None:
                return []

            docs = self.vector_store.similarity_search(
                query,
                k=max_results
            )

            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "document_id": doc.metadata.get("document_id", "unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "metadata": doc.metadata
                })

            return results

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def clear_index(self, document_id: Optional[str] = None):
        """
        Clear the vector store index

        Args:
            document_id: Optional specific document to remove
        """
        if document_id:
            # Delete specific document (would need custom implementation)
            logger.info(f"Clearing index for document: {document_id}")
        else:
            # Clear all
            self.vector_store = None
            logger.info("Cleared all document indexes")
