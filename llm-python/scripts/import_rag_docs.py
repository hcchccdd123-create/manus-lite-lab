#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.rag.ingestion_service import RAGIngestionService


async def main() -> int:
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        service = RAGIngestionService(settings=settings, db=session)
        summary = await service.ingest_directory()

    print(f'Scanned: {summary.scanned}')
    print(f'Imported: {summary.imported}')
    print(f'Skipped: {summary.skipped}')
    print(f'Failed: {summary.failed}')
    if summary.errors:
        print('Errors:')
        for item in summary.errors:
            print(f'- {item}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
