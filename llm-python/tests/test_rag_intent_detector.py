from app.rag.intent_detector import RAGIntentDetector


def test_rag_intent_detector_hits_document_query():
    detector = RAGIntentDetector()

    assert detector.should_retrieve('文档里 chat 接口路径是什么？') is True


def test_rag_intent_detector_skips_creative_query():
    detector = RAGIntentDetector()

    assert detector.should_retrieve('帮我写一个奇幻故事') is False


def test_rag_intent_detector_respects_force_flag():
    detector = RAGIntentDetector()

    assert detector.should_retrieve('随便聊聊', force=True) is True
    assert detector.should_retrieve('文档里有什么', force=False) is False
