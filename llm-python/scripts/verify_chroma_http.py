#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from pprint import pprint

import chromadb

from app.core.config import get_settings


@dataclass(frozen=True)
class SampleRecord:
    id: str
    document: str
    embedding: list[float]
    metadata: dict[str, str]


SAMPLE_RECORDS = [
    SampleRecord(
        id='verify-postgres',
        document='PostgreSQL 是当前 RAG demo 的主业务数据库，负责存储结构化业务数据。',
        embedding=[1.0, 0.0, 0.0],
        metadata={'topic': 'postgresql'},
    ),
    SampleRecord(
        id='verify-chroma',
        document='Chroma HTTP Server 运行在本机 127.0.0.1:8001，提供向量检索能力。',
        embedding=[0.0, 1.0, 0.0],
        metadata={'topic': 'chroma'},
    ),
    SampleRecord(
        id='verify-chat-api',
        document='当前项目的流式聊天接口路径是 POST /api/v1/chat/stream。',
        embedding=[0.0, 0.0, 1.0],
        metadata={'topic': 'chat_api'},
    ),
]

QUERY_EMBEDDING = [0.0, 1.0, 0.0]
QUERY_TEXT = '哪个服务运行在 127.0.0.1:8001 并提供向量检索？'


def main() -> int:
    settings = get_settings()
    print(f'Connecting to Chroma host={settings.chroma_host} port={settings.chroma_port}')
    print(f'Using collection={settings.chroma_collection}')

    try:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        heartbeat = client.heartbeat()
        print(f'Heartbeat OK: {heartbeat}')
    except Exception as exc:
        print(f'ERROR: failed to connect to Chroma HTTP Server: {type(exc).__name__}: {exc}')
        return 1

    try:
        collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={'purpose': 'local_http_validation'},
        )
        print(f'Collection ready: {collection.name}')
    except Exception as exc:
        print(f'ERROR: failed to get or create collection: {type(exc).__name__}: {exc}')
        return 1

    record_ids = [record.id for record in SAMPLE_RECORDS]

    try:
        collection.delete(ids=record_ids)
        print(f'Cleared old test records: {record_ids}')
    except Exception as exc:
        print(f'WARN: could not clear old test records: {type(exc).__name__}: {exc}')

    try:
        collection.add(
            ids=record_ids,
            documents=[record.document for record in SAMPLE_RECORDS],
            embeddings=[record.embedding for record in SAMPLE_RECORDS],
            metadatas=[record.metadata for record in SAMPLE_RECORDS],
        )
        print(f'Inserted {len(SAMPLE_RECORDS)} test records')
    except Exception as exc:
        print(f'ERROR: failed to insert test records: {type(exc).__name__}: {exc}')
        return 1

    try:
        result = collection.query(
            query_embeddings=[QUERY_EMBEDDING],
            n_results=3,
            include=['documents', 'metadatas', 'distances'],
        )
    except Exception as exc:
        print(f'ERROR: failed to query collection: {type(exc).__name__}: {exc}')
        return 1

    print(f'Query text: {QUERY_TEXT}')
    print('Top matches:')
    pprint(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
