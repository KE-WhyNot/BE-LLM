# 테스트 디렉토리

이 폴더에는 프로젝트의 모든 테스트 파일들이 포함되어 있습니다.

## 📁 구조

```
tests/
  ├── test_stock_utils_integration.py  # Stock Utils 통합 테스트
  ├── test_chatbot_workflow.py        # 챗봇 워크플로우 테스트
  ├── portfolio_test.py                # 포트폴리오 제안 테스트
  ├── test_llm_classification.py      # LLM 의도 분류 테스트
  ├── test_google_api.py              # Google API 키 테스트
  └── legacy/                          # 구버전 테스트 파일들
      ├── auto_news_test.py
      ├── news_analysis_test.py
      └── simple_test.py
```

## 🧪 테스트 실행 방법

### 1. Stock Utils 통합 테스트
```bash
python tests/test_stock_utils_integration.py
```

### 2. 챗봇 워크플로우 테스트
```bash
python tests/test_chatbot_workflow.py
```

### 3. 포트폴리오 제안 테스트
```bash
python tests/portfolio_test.py
```

### 4. LLM 의도 분류 테스트
```bash
python tests/test_llm_classification.py
```

### 5. Google API 테스트
```bash
python tests/test_google_api.py
```

## 💬 대화형 테스트

루트 디렉토리에 있는 `test_agent.py`를 사용하여 챗봇과 직접 대화할 수 있습니다:

```bash
python test_agent.py
```

## 📝 주의사항

- 모든 테스트는 프로젝트 루트에서 실행하거나, `sys.path`가 올바르게 설정되어 있어야 합니다.
- `legacy/` 폴더의 파일들은 구버전 코드를 참조하므로 실행되지 않을 수 있습니다.

