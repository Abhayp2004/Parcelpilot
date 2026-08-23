from __future__ import annotations

from typing import Dict, List

from langchain_core.tools import Tool

from backend.data.vectorstore import VectorStore


PRIORITY_LABELS = {
    1: "Customer Agreement",
    2: "Current Policy",
    5: "Deprecated Document",
    6: "Historical Resolution",
}


def _detect_conflicts(results: List[Dict[str, object]], query: str) -> List[str]:
    notices: List[str] = []
    lowered_query = query.lower()
    has_agreement = any(result["metadata"].get("is_customer_agreement") for result in results)  # type: ignore[index]
    has_general_policy = any(result["metadata"].get("priority") == 2 for result in results)  # type: ignore[index]
    if has_agreement and has_general_policy and any(keyword in lowered_query for keyword in ("cancel", "service credit", "sla", "fee")):
        notices.append(
            "⚠ CONFLICT DETECTED: A customer agreement and a general policy both matched. The customer agreement overrides the general policy where they differ."
        )
    if any(result["metadata"].get("priority") == 6 for result in results):  # type: ignore[index]
        notices.append("Historical ticket resolutions are context only and may be incorrect.")
    return notices


def build_search_documents_tool(vector_store: VectorStore) -> Tool:
    def search_documents_func(query: str) -> str:
        results = vector_store.search(query, k=6)
        if not results:
            return "No relevant documents found."

        ordered = sorted(results, key=lambda item: (item["metadata"].get("priority", 99), -item["score"]))
        parts: List[str] = []

        if ordered and all(result["metadata"].get("is_deprecated", False) for result in ordered):
            parts.append("⚠ WARNING: This answer is based on a deprecated document. Verify with current sources.")

        for result in ordered:
            metadata = result["metadata"]
            label = PRIORITY_LABELS.get(metadata.get("priority", 99), "Reference")
            header = f"[SOURCE: {metadata.get('source_file', 'Unknown')} | Priority: {label}]"
            if metadata.get("customer_name"):
                header = f"{header} | Customer: {metadata['customer_name']}"
            parts.append(f"{header}\n{str(result['text']).strip()}")

        parts.extend(_detect_conflicts(ordered, query))
        return "\n\n".join(parts)

    return Tool(
        name="search_documents",
        description="Search policies, SOPs, product guides, and customer agreements to answer questions about rules, entitlements, cancellation terms, service credits, SLAs, and procedures. Use this before data_lookup when the question is about what a policy or contract says.",
        func=search_documents_func,
    )
