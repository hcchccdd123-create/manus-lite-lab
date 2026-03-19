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


def test_should_attempt_rag_defaults_to_true():
    assert ChatService._should_attempt_rag(None) is True
    assert ChatService._should_attempt_rag(True) is True
    assert ChatService._should_attempt_rag(False) is False
