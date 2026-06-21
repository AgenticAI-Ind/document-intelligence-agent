"""
Document comparison and diff analysis
"""

import logging
from typing import Dict, List, Tuple
import difflib
from collections import Counter

logger = logging.getLogger(__name__)


class DocumentComparator:
    """Compare documents and find differences"""

    def __init__(self):
        """Initialize document comparator"""
        pass

    def compare_documents(
        self,
        doc1_content: str,
        doc2_content: str,
        doc1_name: str = "Document 1",
        doc2_name: str = "Document 2"
    ) -> Dict:
        """
        Compare two documents

        Args:
            doc1_content: First document text
            doc2_content: Second document text
            doc1_name: Name of first document
            doc2_name: Name of second document

        Returns:
            Dict with comparison results
        """
        try:
            # Text similarity
            similarity = self._calculate_similarity(doc1_content, doc2_content)

            # Line-by-line diff
            diff = self._generate_diff(doc1_content, doc2_content)

            # Word-level changes
            word_changes = self._analyze_word_changes(doc1_content, doc2_content)

            # Structural comparison
            structure = self._compare_structure(doc1_content, doc2_content)

            return {
                "similarity": similarity,
                "diff": diff,
                "word_changes": word_changes,
                "structure": structure,
                "doc1_name": doc1_name,
                "doc2_name": doc2_name,
                "doc1_length": len(doc1_content),
                "doc2_length": len(doc2_content)
            }

        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {"error": str(e)}

    def _calculate_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate similarity between two texts"""
        # Use SequenceMatcher for similarity ratio
        matcher = difflib.SequenceMatcher(None, text1, text2)
        ratio = matcher.ratio()

        # Quick ratio (faster approximation)
        quick_ratio = matcher.quick_ratio()

        # Character-level stats
        common_chars = sum((Counter(text1) & Counter(text2)).values())
        total_chars = len(text1) + len(text2)
        char_similarity = (2 * common_chars / total_chars) if total_chars > 0 else 0

        return {
            "overall": ratio,
            "quick_estimate": quick_ratio,
            "character_level": char_similarity,
            "percentage": round(ratio * 100, 2)
        }

    def _generate_diff(self, text1: str, text2: str) -> Dict:
        """Generate line-by-line diff"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        # Generate unified diff
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))

        # Categorize changes
        added = []
        removed = []
        changed = []
        unchanged = 0

        for line in diff:
            if line.startswith('+ '):
                added.append(line[2:])
            elif line.startswith('- '):
                removed.append(line[2:])
            elif line.startswith('? '):
                continue  # Skip hint lines
            else:
                unchanged += 1

        # Generate HTML-style diff
        html_diff = difflib.HtmlDiff().make_table(
            lines1,
            lines2,
            fromdesc='Document 1',
            todesc='Document 2',
            context=True,
            numlines=3
        )

        return {
            "added_lines": added,
            "removed_lines": removed,
            "added_count": len(added),
            "removed_count": len(removed),
            "unchanged_count": unchanged,
            "total_changes": len(added) + len(removed),
            "html_diff": html_diff
        }

    def _analyze_word_changes(self, text1: str, text2: str) -> Dict:
        """Analyze word-level changes"""
        words1 = text1.split()
        words2 = text2.split()

        # Word counts
        counter1 = Counter(words1)
        counter2 = Counter(words2)

        # Find added, removed, common words
        all_words = set(words1 + words2)
        added_words = {w: counter2[w] for w in all_words if w in counter2 and w not in counter1}
        removed_words = {w: counter1[w] for w in all_words if w in counter1 and w not in counter2}
        common_words = {w: (counter1[w], counter2[w]) for w in all_words
                       if w in counter1 and w in counter2}

        # Most changed words
        changed_words = {w: (c1, c2) for w, (c1, c2) in common_words.items() if c1 != c2}

        return {
            "added_words": added_words,
            "removed_words": removed_words,
            "changed_frequency": changed_words,
            "total_added": sum(added_words.values()),
            "total_removed": sum(removed_words.values()),
            "word_overlap": len(common_words) / len(all_words) if all_words else 0
        }

    def _compare_structure(self, text1: str, text2: str) -> Dict:
        """Compare document structure"""
        return {
            "lines": {
                "doc1": len(text1.splitlines()),
                "doc2": len(text2.splitlines()),
                "difference": abs(len(text1.splitlines()) - len(text2.splitlines()))
            },
            "words": {
                "doc1": len(text1.split()),
                "doc2": len(text2.split()),
                "difference": abs(len(text1.split()) - len(text2.split()))
            },
            "characters": {
                "doc1": len(text1),
                "doc2": len(text2),
                "difference": abs(len(text1) - len(text2))
            },
            "paragraphs": {
                "doc1": len(text1.split('\n\n')),
                "doc2": len(text2.split('\n\n')),
                "difference": abs(len(text1.split('\n\n')) - len(text2.split('\n\n')))
            }
        }

    def find_duplicates(self, documents: List[Dict]) -> List[Dict]:
        """
        Find duplicate or similar documents

        Args:
            documents: List of dicts with 'id' and 'content'

        Returns:
            List of duplicate pairs
        """
        duplicates = []

        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i+1:], start=i+1):
                similarity = self._calculate_similarity(
                    doc1['content'],
                    doc2['content']
                )

                # Consider documents similar if > 80% match
                if similarity['overall'] > 0.8:
                    duplicates.append({
                        "doc1_id": doc1['id'],
                        "doc2_id": doc2['id'],
                        "similarity": similarity['overall'],
                        "percentage": similarity['percentage']
                    })

        return duplicates

    def highlight_differences(
        self,
        text1: str,
        text2: str,
        context_lines: int = 3
    ) -> List[Dict]:
        """
        Highlight specific differences with context

        Args:
            text1: First document
            text2: Second document
            context_lines: Lines of context around changes

        Returns:
            List of change blocks with context
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        # Get opcodes from SequenceMatcher
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        opcodes = matcher.get_opcodes()

        changes = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag != 'equal':
                # Get context
                context_start1 = max(0, i1 - context_lines)
                context_end1 = min(len(lines1), i2 + context_lines)

                context_start2 = max(0, j1 - context_lines)
                context_end2 = min(len(lines2), j2 + context_lines)

                changes.append({
                    "type": tag,  # replace, delete, insert
                    "doc1_lines": {
                        "start": i1,
                        "end": i2,
                        "content": lines1[i1:i2],
                        "context": lines1[context_start1:context_end1]
                    },
                    "doc2_lines": {
                        "start": j1,
                        "end": j2,
                        "content": lines2[j1:j2],
                        "context": lines2[context_start2:context_end2]
                    }
                })

        return changes

    def semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity (using embeddings if available)

        This is a placeholder for semantic similarity using embeddings
        Falls back to text similarity if embeddings not available
        """
        # TODO: Implement with sentence transformers when available
        # For now, use text-based similarity
        return self._calculate_similarity(text1, text2)['overall']

    def compare_versions(
        self,
        versions: List[Dict]
    ) -> Dict:
        """
        Compare multiple versions of a document

        Args:
            versions: List of dicts with 'version', 'content', 'timestamp'

        Returns:
            Dict with version comparison timeline
        """
        if len(versions) < 2:
            return {"error": "Need at least 2 versions to compare"}

        # Sort by timestamp
        sorted_versions = sorted(versions, key=lambda x: x.get('timestamp', ''))

        comparisons = []

        for i in range(len(sorted_versions) - 1):
            v1 = sorted_versions[i]
            v2 = sorted_versions[i + 1]

            comparison = self.compare_documents(
                v1['content'],
                v2['content'],
                v1.get('version', f'Version {i+1}'),
                v2.get('version', f'Version {i+2}')
            )

            comparisons.append({
                "from_version": v1.get('version'),
                "to_version": v2.get('version'),
                "timestamp": v2.get('timestamp'),
                "comparison": comparison
            })

        return {
            "total_versions": len(versions),
            "comparisons": comparisons
        }
