import inspect

from pipeline.graph import run_pipeline


def test_pipeline_module_exposes_an_async_entrypoint():
    assert inspect.iscoroutinefunction(run_pipeline)
