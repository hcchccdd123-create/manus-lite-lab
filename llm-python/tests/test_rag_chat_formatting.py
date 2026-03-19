import asyncio
from types import SimpleNamespace

from app.rag.types import RAG_MISS_NOTICE, RetrievedContext
from app.services.chat_service import ChatService


def test_append_rag_source_summary_appends_sources():
    context = RetrievedContext(
        found=True,
        source_summary='来源摘要：\n1. FAQ (docs/faq.md)',
    )

    result = ChatService._append_rag_source_summary('这是回答', context)

    assert result.endswith('来源摘要：\n1. FAQ (docs/faq.md)')


def test_rag_miss_notice_constant_is_stable():
    assert RAG_MISS_NOTICE.startswith('未命中任何文档')


def test_doc_queries_disable_thinking_by_default():
    assert ChatService._resolve_enable_thinking('glm', None, prefer_concise_answer=True) is False
    assert ChatService._resolve_enable_thinking('ollama', None, prefer_concise_answer=True) is False


def test_non_doc_queries_keep_provider_thinking_default():
    assert ChatService._resolve_enable_thinking('glm', None, prefer_concise_answer=False) is True
    assert ChatService._resolve_enable_thinking('codex', None, prefer_concise_answer=True) is False


def test_resolve_rag_decision_respects_global_gate_and_intent():
    service = ChatService.__new__(ChatService)
    service.settings = SimpleNamespace(rag_enabled=True)

    class StubDetector:
        @staticmethod
        def should_retrieve(query: str, force: bool | None = None) -> bool:
            if force is not None:
                return force
            return '文档里' in query

    service.rag_intent_detector = StubDetector()

    doc_decision = service._resolve_rag_decision(message='文档里 chat 接口路径是什么？', force=None)
    assert doc_decision.enabled is True
    assert doc_decision.override is None
    assert doc_decision.intent_matched is True
    assert doc_decision.should_retrieve is True

    casual_decision = service._resolve_rag_decision(message='随便聊聊', force=None)
    assert casual_decision.enabled is True
    assert casual_decision.override is None
    assert casual_decision.intent_matched is False
    assert casual_decision.should_retrieve is False

    forced_decision = service._resolve_rag_decision(message='随便聊聊', force=True)
    assert forced_decision.enabled is True
    assert forced_decision.override is True
    assert forced_decision.intent_matched is True
    assert forced_decision.should_retrieve is True

    disabled_decision = service._resolve_rag_decision(message='文档里有什么', force=False)
    assert disabled_decision.enabled is True
    assert disabled_decision.override is False
    assert disabled_decision.intent_matched is False
    assert disabled_decision.should_retrieve is False


def test_resolve_rag_decision_global_off_blocks_even_forced_requests():
    service = ChatService.__new__(ChatService)
    service.settings = SimpleNamespace(rag_enabled=False)

    class StubDetector:
        @staticmethod
        def should_retrieve(query: str, force: bool | None = None) -> bool:
            return True

    service.rag_intent_detector = StubDetector()

    forced_decision = service._resolve_rag_decision(message='文档里 chat 接口路径是什么？', force=True)
    assert forced_decision.enabled is False
    assert forced_decision.override is True
    assert forced_decision.intent_matched is True
    assert forced_decision.should_retrieve is False

    default_decision = service._resolve_rag_decision(message='文档里 chat 接口路径是什么？', force=None)
    assert default_decision.enabled is False
    assert default_decision.override is None
    assert default_decision.intent_matched is True
    assert default_decision.should_retrieve is False


def test_maybe_retrieve_rag_context_attempts_retrieval_for_doc_query_without_override():
    service = ChatService.__new__(ChatService)
    service.settings = SimpleNamespace(rag_enabled=True)

    class StubDetector:
        @staticmethod
        def should_retrieve(query: str, force: bool | None = None) -> bool:
            return '文档里' in query

    class StubRetriever:
        def __init__(self):
            self.calls: list[str] = []

        async def retrieve(self, query: str) -> RetrievedContext:
            self.calls.append(query)
            return RetrievedContext(found=True, prompt_context='ctx', source_summary='src')

    service.rag_intent_detector = StubDetector()
    service.rag_retriever = StubRetriever()
    decision = service._resolve_rag_decision(message='文档里 chat 接口路径是什么？', force=None)

    result = asyncio.run(
        service._maybe_retrieve_rag_context(
            message='文档里 chat 接口路径是什么？',
            decision=decision,
        )
    )

    assert service.rag_retriever.calls == ['文档里 chat 接口路径是什么？']
    assert result is not None
    assert result.found is True
