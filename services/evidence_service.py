from typing import List, Dict, Any

class EvidenceService:
    @staticmethod
    def construct_evidence_block(tool_name: str, query_executed: str, data_returned: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Packages explicit query contexts to anchor responses and provide verifiable citations."""
        return {
            "source_tool": tool_name,
            "query_context": query_executed,
            "record_count": len(data_returned),
            "sample_records": data_returned[:3]  # Truncated sample to limit downstream context bloat
        }
