#!/usr/bin/env python3
"""
프롬프트 관리자 테스트
새로운 프롬프트 시스템 테스트
"""

import os
from typing import Dict, Any

# 환경변수 설정
os.environ['PRIMARY_MODEL'] = 'gemini-2.0-flash-exp'
os.environ['FALLBACK_MODEL'] = 'gemini-2.0-flash-exp'
os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash-exp'

from app.services.langgraph_enhanced.prompt_manager import prompt_manager
from app.services.langgraph_enhanced.llm_manager import get_gemini_llm


class PromptManagerTester:
    """프롬프트 관리자 테스터"""
    
    def __init__(self):
        self.prompt_manager = prompt_manager
        self.llm = get_gemini_llm(temperature=0.1)
        
        # 테스트 데이터
        self.test_financial_data = {
            'symbol': '005930.KS',
            'company_name': '삼성전자',
            'current_price': 75000,
            'price_change_percent': 2.5,
            'volume': 8500000,
            'market_cap': '450조원',
            'pe_ratio': 12.5,
            'pbr': 1.2,
            'roe': 18.5,
            'debt_to_equity': 85.2,
            'sector': '반도체'
        }
        
        self.test_news_data = [
            {
                'title': '삼성전자, 3분기 실적 발표...영업이익 증가',
                'summary': '삼성전자가 3분기 실적을 발표하며 영업이익이 전년 대비 증가했다고 발표했습니다.',
                'date': '2024-10-04'
            },
            {
                'title': '반도체 시장 회복 신호 포착',
                'summary': '글로벌 반도체 시장에서 회복 신호가 포착되며 삼성전자 등 관련주에 관심이 집중되고 있습니다.',
                'date': '2024-10-03'
            }
        ]
        
        self.test_knowledge_context = """
        PER(Price-to-Earnings Ratio)은 주가수익비율을 의미하는 투자 지표입니다.
        주가를 주당순이익(EPS)으로 나눈 값으로, 주식이 얼마나 비싸거나 싸게 거래되고 있는지를 나타냅니다.
        낮은 PER은 저평가를, 높은 PER은 고평가를 의미할 수 있습니다.
        """
    
    def run_prompt_tests(self):
        """프롬프트 테스트 실행"""
        print("🚀 프롬프트 관리자 테스트")
        print("=" * 60)
        
        # 1. 분류 프롬프트 테스트
        self._test_classification_prompts()
        
        # 2. 분석 프롬프트 테스트
        self._test_analysis_prompts()
        
        # 3. 뉴스 프롬프트 테스트
        self._test_news_prompts()
        
        # 4. 지식 프롬프트 테스트
        self._test_knowledge_prompts()
        
        # 5. 실제 LLM 응답 테스트
        self._test_llm_responses()
    
    def _test_classification_prompts(self):
        """분류 프롬프트 테스트"""
        print("\n📋 1. 분류 프롬프트 테스트")
        print("-" * 40)
        
        test_queries = [
            "삼성전자 주가 알려줘",
            "PER이 뭐야?",
            "삼성전자 투자해도 될까?",
            "삼성전자 뉴스 알려줘",
            "안녕하세요"
        ]
        
        for query in test_queries:
            prompt = self.prompt_manager.generate_classification_prompt(query)
            print(f"\n🔍 쿼리: {query}")
            print(f"📝 생성된 프롬프트 길이: {len(prompt)}자")
            print(f"📄 프롬프트 미리보기: {prompt[:200]}...")
    
    def _test_analysis_prompts(self):
        """분석 프롬프트 테스트"""
        print(f"\n📊 2. 분석 프롬프트 테스트")
        print("-" * 40)
        
        # 기본 분석 프롬프트
        basic_prompt = self.prompt_manager.generate_analysis_prompt(
            self.test_financial_data,
            "삼성전자 투자해도 될까?"
        )
        
        print(f"📝 기본 분석 프롬프트 길이: {len(basic_prompt)}자")
        print(f"📄 프롬프트 미리보기: {basic_prompt[:300]}...")
        
        # 동적 분석 프롬프트 (사용자 프로필 포함)
        user_context = {
            "user_profile": {
                "experience_level": "초급",
                "interests": "안정적 투자",
                "risk_tolerance": "낮음",
                "investment_goals": "장기 투자"
            }
        }
        
        dynamic_prompt = self.prompt_manager.generate_analysis_prompt(
            self.test_financial_data,
            "삼성전자 투자해도 될까?",
            user_context
        )
        
        print(f"\n📝 동적 분석 프롬프트 길이: {len(dynamic_prompt)}자")
        print(f"📄 프롬프트 미리보기: {dynamic_prompt[:300]}...")
    
    def _test_news_prompts(self):
        """뉴스 프롬프트 테스트"""
        print(f"\n📰 3. 뉴스 프롬프트 테스트")
        print("-" * 40)
        
        prompt = self.prompt_manager.generate_news_prompt(
            self.test_news_data,
            "삼성전자 뉴스 알려줘"
        )
        
        print(f"📝 뉴스 프롬프트 길이: {len(prompt)}자")
        print(f"📄 프롬프트 미리보기: {prompt[:300]}...")
    
    def _test_knowledge_prompts(self):
        """지식 프롬프트 테스트"""
        print(f"\n📚 4. 지식 프롬프트 테스트")
        print("-" * 40)
        
        prompt = self.prompt_manager.generate_knowledge_prompt(
            self.test_knowledge_context,
            "PER이 뭐야?"
        )
        
        print(f"📝 지식 프롬프트 길이: {len(prompt)}자")
        print(f"📄 프롬프트 미리보기: {prompt[:300]}...")
    
    def _test_llm_responses(self):
        """실제 LLM 응답 테스트"""
        print(f"\n🤖 5. 실제 LLM 응답 테스트")
        print("-" * 40)
        
        try:
            # 분류 테스트
            classification_prompt = self.prompt_manager.generate_classification_prompt("삼성전자 주가 알려줘")
            classification_response = self.llm.invoke(classification_prompt)
            print(f"✅ 분류 응답: {classification_response.content.strip()}")
            
            # 지식 테스트 (간단한 버전)
            knowledge_prompt = self.prompt_manager.generate_knowledge_prompt(
                self.test_knowledge_context,
                "PER이 뭐야?"
            )
            knowledge_response = self.llm.invoke(knowledge_prompt)
            print(f"✅ 지식 응답 길이: {len(knowledge_response.content)}자")
            print(f"📄 지식 응답 미리보기: {knowledge_response.content[:200]}...")
            
        except Exception as e:
            print(f"❌ LLM 응답 테스트 실패: {e}")
    
    def _test_prompt_templates(self):
        """프롬프트 템플릿 테스트"""
        print(f"\n📋 6. 프롬프트 템플릿 구조 테스트")
        print("-" * 40)
        
        templates = self.prompt_manager.prompt_templates
        
        print(f"📚 사용 가능한 템플릿 카테고리:")
        for category, template_data in templates.items():
            print(f"   • {category}: {len(template_data)}개 템플릿")
            
            for template_type, content in template_data.items():
                if isinstance(content, str):
                    print(f"     - {template_type}: {len(content)}자")
                elif isinstance(content, list):
                    print(f"     - {template_type}: {len(content)}개 예시")
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        self.run_prompt_tests()
        self._test_prompt_templates()
        
        print(f"\n🎯 프롬프트 관리자 특징:")
        print("   🧠 동적 프롬프트 생성")
        print("   👤 사용자 프로필 반영")
        print("   📊 컨텍스트 기반 맞춤형 프롬프트")
        print("   🔄 템플릿 기반 재사용 가능한 구조")
        print("   ⚡ Gemini 2.0 Flash 최적화")
        
        print(f"\n💡 사용 방법:")
        print("   from app.services.langgraph_enhanced import prompt_manager")
        print("   prompt = prompt_manager.generate_analysis_prompt(data, query)")
        print("   response = llm.invoke(prompt)")


if __name__ == "__main__":
    tester = PromptManagerTester()
    tester.run_comprehensive_test()
