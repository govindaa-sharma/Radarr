import pytest

from agents.crawler import run_crawler


@pytest.mark.asyncio
async def test_crawler_rejects_non_positive_concurrency():
    with pytest.raises(ValueError, match="at least 1"):
        await run_crawler(max_concurrent=0)
