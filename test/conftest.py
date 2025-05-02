import pytest

# 使用 pytest 钩子设置 asyncio 默认 fixture 循环作用域


def pytest_addoption(parser):
    parser.addini(
        'asyncio_default_fixture_loop_scope',
        help='default fixture loop scope',
        default='function'
    )
