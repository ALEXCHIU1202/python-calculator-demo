"""
pytest 全域設定
確保 alpacabot/ 根目錄在 sys.path 中，讓所有測試可以正確 import
"""
import sys
from pathlib import Path

# 將 alpacabot/ 加入路徑（tests/ 的上層目錄）
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
