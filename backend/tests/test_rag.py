import unittest
from pathlib import Path

from langchain_core.documents import Document
from pydantic import ValidationError

from app.agent.tool_executor import execute_tool
from app.agent.tools import TOOLS
from app.agent.tools.retrieve_product_knowledge import (
    RetrieveProductKnowledgeInput,
)
from app.rag.embeddings import (
    EMBEDDING_DIMENSION,
    EmbeddingDimensionError,
    validate_embedding,
)
from app.rag.retriever import document_to_retrieval_hit
from app.rag.splitter import split_markdown_document
from scripts.seed_catalog import CATALOG


class RagUnitTests(unittest.TestCase):
    def test_production_tool_set_has_exactly_four_tools(self) -> None:
        self.assertEqual(
            [tool.name for tool in TOOLS],
            [
                "search_products",
                "get_product_detail",
                "check_inventory",
                "retrieve_product_knowledge",
            ],
        )

    def test_splitter_preserves_product_and_topic_context(self) -> None:
        chunks = split_markdown_document(
            "# Demo Phone\n\n## Camera\n\nChụp đêm rõ nét và giữ màu tự nhiên.",
            source_name="demo-phone.md",
            product_name="Demo Phone",
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].topic, "Camera and video")
        self.assertIn("Product: Demo Phone", chunks[0].embedding_text)
        self.assertIn("Topic: Camera", chunks[0].embedding_text)
        self.assertEqual(len(chunks[0].content_hash), 64)

    def test_all_seeded_products_have_knowledge_files(self) -> None:
        knowledge_dir = Path(__file__).parents[1] / "data" / "knowledge"
        expected_slugs = {item["product"]["slug"] for item in CATALOG}
        actual_slugs = {file.stem for file in knowledge_dir.glob("*.md")}

        self.assertEqual(actual_slugs, expected_slugs)

    def test_embedding_dimension_validation(self) -> None:
        vector = validate_embedding([0.0] * EMBEDDING_DIMENSION)
        self.assertEqual(len(vector), EMBEDDING_DIMENSION)

    def test_embedding_dimension_rejects_wrong_shape(self) -> None:
        with self.assertRaises(EmbeddingDimensionError):
            validate_embedding([0.0] * (EMBEDDING_DIMENSION - 1))

    def test_retrieval_input_normalizes_query_and_ids(self) -> None:
        payload = RetrieveProductKnowledgeInput(
            query="  camera đêm  ",
            product_ids=[7, 9],
            top_k=5,
        )

        self.assertEqual(payload.query, "camera đêm")
        self.assertEqual(payload.product_ids, [7, 9])

    def test_retrieval_input_rejects_invalid_values(self) -> None:
        invalid_payloads = [
            {"query": "", "top_k": 5},
            {"query": "camera", "top_k": 100},
            {"query": "camera", "product_ids": []},
            {"query": "camera", "product_ids": [-1]},
            {"query": "camera", "product_ids": [7, 7]},
        ]

        for invalid_payload in invalid_payloads:
            with self.subTest(payload=invalid_payload):
                with self.assertRaises(ValidationError):
                    RetrieveProductKnowledgeInput.model_validate(invalid_payload)

    def test_invalid_tool_args_do_not_execute_retrieval(self) -> None:
        async def run() -> None:
            execution = await execute_tool(
                {
                    "id": "invalid-args",
                    "name": "retrieve_product_knowledge",
                    "args": {"query": "", "top_k": 100},
                },
                session=None,  # type: ignore[arg-type]
            )
            self.assertEqual(execution.status, "error")
            self.assertEqual(execution.result["error"], "invalid_arguments")

        import asyncio

        asyncio.run(run())

    def test_retrieval_hit_does_not_expose_embedding(self) -> None:
        hit = document_to_retrieval_hit(
            Document(
                page_content="Camera experience",
                metadata={
                    "product_id": 7,
                    "slug": "demo-phone",
                    "name": "Demo Phone",
                    "topic": "Camera",
                    "source_name": "demo-phone.md",
                    "chunk_index": 0,
                    "cosine_distance": 0.18,
                },
            )
        )

        self.assertEqual(hit["product_id"], 7)
        self.assertNotIn("embedding", hit)
        self.assertNotIn("vector", hit)


if __name__ == "__main__":
    unittest.main()
