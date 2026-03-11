from __future__ import annotations

from pageindex.retrieval_schema import (
    ExtractedContext,
    RetrievalDocument,
    RetrievalError,
    RetrievalNode,
    RetrievalResult,
)


def test_retrieval_result_defaults_to_flat_selected_nodes():
    result = RetrievalResult(
        query="box parser registry",
        corpus_root="/tmp/corpus",
        catalog_path="/tmp/catalog.json",
        candidate_documents=[_document("doc-1", ranking_score=0.91)],
        selected_documents=[_document("doc-1")],
        selected_nodes=[
            RetrievalNode(
                record_id="doc-1",
                node_id="n-1",
                title="BoxHeader",
                source_path="/tmp/corpus/TASK_BoxHeader.md",
                output_path="/tmp/output/TASK_BoxHeader_structure.json",
                summary="Defines BoxHeader",
                line_number=12,
                reasoning="high lexical overlap",
            )
        ],
        extracted_context=[
            ExtractedContext(
                record_id="doc-1",
                node_id="n-1",
                text="BoxHeader is the protocol entry point.",
                citation="TASK_BoxHeader.md:12",
            )
        ],
    )

    payload = result.to_dict()

    assert list(payload) == [
        "schema_version",
        "query",
        "corpus_root",
        "catalog_path",
        "candidate_documents",
        "selected_documents",
        "selected_nodes",
        "extracted_context",
        "errors",
    ]
    assert payload["selected_nodes"] == [
        {
            "record_id": "doc-1",
            "node_id": "n-1",
            "title": "BoxHeader",
            "source_path": "/tmp/corpus/TASK_BoxHeader.md",
            "output_path": "/tmp/output/TASK_BoxHeader_structure.json",
            "summary": "Defines BoxHeader",
            "line_number": 12,
        }
    ]
    assert "grouped_documents" not in payload


def test_retrieval_result_supports_grouped_output_and_reasoning():
    document = _document("doc-1")
    result = RetrievalResult(
        query="parse tree",
        corpus_root="/tmp/corpus",
        catalog_path="/tmp/catalog.json",
        selected_documents=[document],
        selected_nodes=[
            RetrievalNode(
                record_id="doc-1",
                node_id="n-1",
                title="ParseTree",
                source_path="/tmp/corpus/TASK_ParseTree.md",
                output_path="/tmp/output/TASK_ParseTree_structure.json",
                reasoning="matched candidate title",
            )
        ],
    )

    payload = result.to_dict(group_by_document=True, include_reasoning=True)

    assert payload["selected_nodes"][0]["reasoning"] == "matched candidate title"
    assert payload["grouped_documents"] == [
        {
            "document": {
                "record_id": "doc-1",
                "document_name": "TASK_ParseTree",
                "document_type": "task",
                "source_path": "/tmp/corpus/TASK_ParseTree.md",
                "output_path": "/tmp/output/TASK_ParseTree_structure.json",
                "source_rel_path": "TASK_ParseTree.md",
                "output_rel_path": "TASK_ParseTree_structure.json",
                "freshness_timestamp": "2026-03-11",
            },
            "selected_nodes": [
                {
                    "record_id": "doc-1",
                    "node_id": "n-1",
                    "title": "ParseTree",
                    "source_path": "/tmp/corpus/TASK_ParseTree.md",
                    "output_path": "/tmp/output/TASK_ParseTree_structure.json",
                    "reasoning": "matched candidate title",
                }
            ],
        }
    ]


def test_retrieval_result_serializes_machine_readable_errors():
    result = RetrievalResult(
        query="broken query",
        corpus_root="/tmp/corpus",
        catalog_path="/tmp/catalog.json",
        errors=[
            RetrievalError(
                code="lm_unavailable",
                message="LM Studio request failed",
                details={"status": 503},
            )
        ],
    )

    payload = result.to_dict()

    assert payload["errors"] == [
        {
            "code": "lm_unavailable",
            "message": "LM Studio request failed",
            "details": {"status": 503},
        }
    ]


def _document(record_id: str, ranking_score: float | None = None) -> RetrievalDocument:
    return RetrievalDocument(
        record_id=record_id,
        document_name="TASK_ParseTree",
        document_type="task",
        source_path="/tmp/corpus/TASK_ParseTree.md",
        output_path="/tmp/output/TASK_ParseTree_structure.json",
        source_rel_path="TASK_ParseTree.md",
        output_rel_path="TASK_ParseTree_structure.json",
        freshness_timestamp="2026-03-11",
        ranking_score=ranking_score,
    )
