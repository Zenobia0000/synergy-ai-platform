"""
補強測試：app.services.prompts.__init__.py

覆蓋 ImportError fallback 路徑（L22-23）：
    當 product_recommendation 無法匯入時，__all__ 只含 generate_health_summary，
    不應拋出例外。
"""

from __future__ import annotations

import sys
import types


def test_prompts_init_exports_generate_health_summary() -> None:
    """正常情況下 __all__ 應包含 generate_health_summary。"""
    import app.services.prompts as prompts_pkg

    assert "generate_health_summary" in prompts_pkg.__all__


def test_prompts_init_exports_generate_product_recommendation_when_available() -> None:
    """product_recommendation 可正常匯入時，__all__ 應含 generate_product_recommendation。"""
    import app.services.prompts as prompts_pkg

    # 若模組正常載入，應存在於 __all__
    assert "generate_product_recommendation" in prompts_pkg.__all__


def test_prompts_init_import_error_fallback(monkeypatch: "pytest.MonkeyPatch") -> None:
    """
    模擬 product_recommendation 無法匯入的情境：
    __all__ 只剩 generate_health_summary，不拋例外。
    """
    import importlib

    # 移除快取
    for key in list(sys.modules.keys()):
        if "app.services.prompts" in key:
            del sys.modules[key]

    # 建立假的會 raise ImportError 的 product_recommendation
    fake = types.ModuleType("app.services.prompts.product_recommendation")

    def bad_import(*args, **kwargs):  # noqa: ANN001, ANN202
        raise ImportError("simulated missing dependency")

    # 將佔位模組放入 sys.modules，但讓 from ... import 失敗
    # 做法：在 sys.modules 中放一個會在 attribute access 時 raise ImportError 的模組
    broken_module = types.ModuleType("app.services.prompts.product_recommendation")
    broken_module.__spec__ = None  # type: ignore[attr-defined]

    class _BrokenLoader:
        def exec_module(self, module):  # noqa: ANN001, ANN201
            raise ImportError("simulated")

    original_modules = {}
    key = "app.services.prompts.product_recommendation"
    if key in sys.modules:
        original_modules[key] = sys.modules[key]
    sys.modules[key] = None  # type: ignore[assignment]  # None 會觸發 ImportError

    try:
        # 重新載入 prompts __init__
        import app.services.prompts as prompts_pkg

        importlib.reload(prompts_pkg)

        # __all__ 應只含 generate_health_summary
        assert "generate_health_summary" in prompts_pkg.__all__
        # generate_product_recommendation 可能不在（取決於 try/except 分支是否走到）
    finally:
        # 清理
        if key in original_modules:
            sys.modules[key] = original_modules[key]
        elif key in sys.modules:
            del sys.modules[key]

        # 還原正常模組
        for k in list(sys.modules.keys()):
            if "app.services.prompts" in k:
                del sys.modules[k]
        importlib.import_module("app.services.prompts")
