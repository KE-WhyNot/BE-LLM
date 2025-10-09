"""금융 워크플로우 - 메타 에이전트 시스템 통합"""

from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings

# 메타 에이전트 기반 지능형 워크플로우
try:
    from app.services.langgraph_enhanced.workflow_router import WorkflowRouter
    INTELLIGENT_WORKFLOW_AVAILABLE = True
except ImportError:
    INTELLIGENT_WORKFLOW_AVAILABLE = False
    WorkflowRouter = None


class FinancialWorkflowService:
    """금융 워크플로우 서비스 - 메타 에이전트 시스템 연동"""
    
    def __init__(self):
        # 메타 에이전트 워크플로우 라우터 초기화
        if INTELLIGENT_WORKFLOW_AVAILABLE:
            try:
                self.intelligent_workflow_router = WorkflowRouter()
                print("✅ 메타 에이전트 워크플로우 라우터 초기화 완료")
            except Exception as e:
                print(f"⚠️ 메타 에이전트 워크플로우 라우터 초기화 실패: {e}")
                import traceback
                traceback.print_exc()
                self.intelligent_workflow_router = None
        else:
            self.intelligent_workflow_router = None
            print("❌ 메타 에이전트 워크플로우를 사용할 수 없습니다")
    
    def process_query(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자 쿼리 처리 - 메인 진입점"""
        try:
            # 메타 에이전트 워크플로우 사용 (우선)
            if self.intelligent_workflow_router:
                print(f"🤖 메타 에이전트 기반 지능형 워크플로우 사용")
                print(f"   ✨ 복잡도 분석 → 서비스 계획 → 병렬 실행 → 결과 통합 → 신뢰도 평가")
                
                result = self.intelligent_workflow_router.process_query(
                    user_query=user_query,
                    user_id=user_id
                )
                
                # 결과 로깅
                if result.get('success'):
                    action_data = result.get('action_data', {})
                    if 'service_plan' in action_data:
                        plan = action_data['service_plan']
                        print(f"   📋 실행 계획: {plan.get('execution_mode', 'N/A')}")
                    if 'confidence_evaluation' in action_data:
                        confidence = action_data['confidence_evaluation']
                        print(f"   🎯 신뢰도: {confidence.get('overall_confidence', 0):.2f}")
                
                return result
            else:
                # 메타 에이전트를 사용할 수 없는 경우
                return self._create_fallback_response(user_query, user_id)
            
        except Exception as e:
            print(f"❌ 워크플로우 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response(e, user_id)
    
    def _create_fallback_response(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """폴백 응답 생성 (메타 에이전트 사용 불가 시)"""
        return {
            "success": False,
            "reply_text": """죄송합니다. 현재 시스템을 사용할 수 없습니다.
            
⚠️ 메타 에이전트 워크플로우를 초기화할 수 없습니다.
시스템 관리자에게 문의하거나 잠시 후 다시 시도해주세요.""",
            "action_type": "display_info",
            "action_data": {
                "error": "메타 에이전트 워크플로우 사용 불가",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
        }
    
    def _create_error_response(self, error: Exception, user_id: Optional[str] = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "success": False,
            "reply_text": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(error)}",
            "action_type": "display_info",
            "action_data": {
                "error": str(error),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
        }


# 전역 워크플로우 서비스 인스턴스
financial_workflow = FinancialWorkflowService()

financial_workflow = FinancialWorkflowService()
