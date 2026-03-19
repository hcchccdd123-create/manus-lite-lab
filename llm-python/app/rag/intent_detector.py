from __future__ import annotations


class RAGIntentDetector:
    _EXPLICIT_HINTS = (
        '文档',
        '手册',
        '知识库',
        '说明',
        '接口文档',
        'faq',
        '文档里',
        '资料里',
        'readme',
        '配置项',
        '部署',
        '启动',
        '路径',
        '端口',
        '接口',
    )

    _PROJECT_HINTS = (
        'chat/stream',
        'db_url',
        'postgresql',
        'chroma',
        'glm',
        'provider',
        'memory',
        'thinking',
        '会话',
        '消息',
        '摘要',
        '流式',
        '配置',
        '脚本',
    )

    _NEGATIVE_HINTS = (
        '写一篇',
        '写一个故事',
        '脑洞',
        '创作',
        '翻译',
        '诗',
        '实时',
        '最新新闻',
        '天气',
    )

    def should_retrieve(self, query: str, force: bool | None = None) -> bool:
        if force is True:
            return True
        if force is False:
            return False

        lowered = query.lower()
        if any(token in lowered for token in self._NEGATIVE_HINTS):
            return False
        if any(token in lowered for token in self._EXPLICIT_HINTS):
            return True
        return any(token in lowered for token in self._PROJECT_HINTS)
