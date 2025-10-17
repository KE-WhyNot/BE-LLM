import os
import sys


# 프로젝트 루트를 PYTHONPATH에 추가하여 `app` 모듈 임포트 가능하게 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


