"""재무제표 데이터 조회 및 분석 서비스"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from app.services.pinecone_rag_service import search_pinecone, get_context_for_query
from app.services.pinecone_config import KNOWLEDGE_NAMESPACES
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class FinancialDataService:
    """Pinecone 재무제표 데이터 조회 및 분석 서비스"""
    
    def __init__(self):
        self.financial_namespace = KNOWLEDGE_NAMESPACES.get("financial_analysis", "cat_financial_statements")
        self.llm = self._initialize_llm()
        
        # 투자 성향별 재무지표 기준
        self.financial_criteria = {
            "안정형": {
                "priorities": ["stability", "dividend", "low_debt"],
                "key_metrics": ["ROE", "부채비율", "배당수익률", "순이익"],
                "thresholds": {
                    "ROE": {"min": 10, "preferred": 15},
                    "부채비율": {"max": 50, "preferred": 30},
                    "배당수익률": {"min": 2, "preferred": 4}
                }
            },
            "안정추구형": {
                "priorities": ["stability", "growth", "dividend"],
                "key_metrics": ["ROE", "매출성장률", "영업이익", "배당수익률"],
                "thresholds": {
                    "ROE": {"min": 8, "preferred": 12},
                    "매출성장률": {"min": 3, "preferred": 8},
                    "부채비율": {"max": 60, "preferred": 40}
                }
            },
            "위험중립형": {
                "priorities": ["balance", "growth", "stability"],
                "key_metrics": ["PER", "PBR", "ROE", "매출성장률"],
                "thresholds": {
                    "PER": {"min": 5, "max": 20, "preferred_max": 15},
                    "PBR": {"min": 0.5, "max": 3, "preferred_max": 2},
                    "ROE": {"min": 5, "preferred": 10}
                }
            },
            "적극투자형": {
                "priorities": ["growth", "revenue_expansion", "market_share"],
                "key_metrics": ["매출성장률", "영업이익증가율", "시장점유율", "R&D투자"],
                "thresholds": {
                    "매출성장률": {"min": 10, "preferred": 20},
                    "영업이익증가율": {"min": 15, "preferred": 30},
                    "PER": {"max": 30}  # 성장주는 PER이 높아도 허용
                }
            },
            "공격투자형": {
                "priorities": ["high_growth", "innovation", "market_disruption"],
                "key_metrics": ["매출성장률", "영업이익증가율", "신사업매출", "기술투자"],
                "thresholds": {
                    "매출성장률": {"min": 20, "preferred": 50},
                    "영업이익증가율": {"min": 25, "preferred": 100},
                    "부채비율": {"max": 80}  # 성장을 위한 부채는 허용
                }
            }
        }
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.2,
                google_api_key=settings.google_api_key
            )
        return None
    
    async def get_financial_analysis(
        self,
        stock_code: str,
        stock_name: str,
        investment_profile: str
    ) -> Dict[str, Any]:
        """특정 종목의 재무 분석 정보 조회"""
        
        financial_analysis_start = time.time()
        
        try:
            print(f"📊 {stock_name} ({stock_code}) 재무 분석 조회...")
            
            # 1. Pinecone에서 재무제표 데이터 검색
            search_start = time.time()
            financial_data = await self._search_financial_data(stock_code, stock_name)
            search_time = time.time() - search_start
            print(f"  🔍 재무 데이터 검색: {search_time:.3f}초 ({len(financial_data) if financial_data else 0}개)")
            
            if not financial_data:
                total_time = time.time() - financial_analysis_start
                print(f"⚠️ {stock_name} 재무 데이터 없음, 기본 분석 반환 ({total_time:.3f}초)")
                return self._get_default_financial_analysis(stock_code, stock_name)
            
            # 2. 투자 성향별 재무지표 분석
            metrics_start = time.time()
            criteria = self.financial_criteria.get(investment_profile)
            analysis = await self._analyze_financial_metrics(
                financial_data, 
                criteria, 
                stock_name,
                investment_profile
            )
            metrics_time = time.time() - metrics_start
            print(f"  📈 재무지표 분석: {metrics_time:.3f}초")
            
            result_processing_start = time.time()
            result = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "investment_profile": investment_profile,
                "financial_score": analysis.get("financial_score", 50),
                "key_metrics": analysis.get("key_metrics", {}),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "recommendation": analysis.get("recommendation", "보통"),
                "analysis_summary": analysis.get("analysis_summary", ""),
                "data_sources": len(financial_data),
                "analysis_date": analysis.get("analysis_date", "")
            }
            result_processing_time = time.time() - result_processing_start
            print(f"  📋 결과 처리: {result_processing_time:.3f}초")
            
            total_time = time.time() - financial_analysis_start
            print(f"✅ {stock_name} 재무 분석 완료: 점수 {result['financial_score']}/100 ({total_time:.3f}초)")
            
            return result
            
        except Exception as e:
            total_time = time.time() - financial_analysis_start
            print(f"❌ {stock_name} 재무 분석 실패 ({total_time:.3f}초): {e}")
            return self._get_default_financial_analysis(stock_code, stock_name)
    
    async def _search_financial_data(
        self, 
        stock_code: str, 
        stock_name: str
    ) -> List[Dict[str, Any]]:
        """Pinecone에서 재무제표 데이터 검색"""
        
        from app.services.pinecone_rag_service import PineconeRAGService
        
        rag_service = PineconeRAGService()
        rag_service.initialize()
        
        # 다양한 쿼리로 재무 데이터 검색 (파일명 기반 + 내용 기반)
        search_queries = [
            f"[{stock_name}]반기보고서",  # 파일명 직접 매칭
            f"[{stock_name}]",             # 파일명 패턴
            f"{stock_name} 재무상태표",    # 재무제표 섹션
            f"{stock_name} 손익계산서",    # 손익 섹션
            f"{stock_name} 자산 부채",     # 재무 건전성
            f"{stock_name} 매출 영업이익", # 성과 지표
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                # Pinecone 검색 (더 많은 결과 가져오기)
                results = await asyncio.to_thread(
                    lambda q=query: search_pinecone(q, namespace=self.financial_namespace, top_k=5)
                )
                
                # QueryResponse 객체 처리
                if results and hasattr(results, 'matches') and results.matches:
                    for match in results.matches:
                        formatted_result = {
                            "id": match.id,
                            "score": match.score,
                            "text": match.metadata.get("text", "") if hasattr(match, 'metadata') and match.metadata else "",
                            "metadata": match.metadata if hasattr(match, 'metadata') else {}
                        }
                        # 텍스트가 있는 경우에만 추가
                        if formatted_result["text"]:
                            all_results.append(formatted_result)
                
                # API 부하 방지
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"⚠️ 재무 데이터 검색 실패 ({query}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 중복 제거 및 관련도 높은 결과만 반환
        unique_results = self._remove_duplicate_financial_data(all_results)
        return unique_results[:10]  # 상위 10개만
    
    async def _analyze_financial_metrics(
        self,
        financial_data: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        stock_name: str,
        investment_profile: str
    ) -> Dict[str, Any]:
        """재무지표 분석 (LLM 활용)"""
        
        if not self.llm or not financial_data:
            return self._fallback_financial_analysis(stock_name, criteria)
        
        # 재무 데이터 텍스트 추출
        financial_texts = []
        for data in financial_data:
            content = data.get('text', data.get('content', ''))
            metadata = data.get('metadata', {})
            financial_texts.append(f"출처: {metadata.get('source', 'Unknown')}\n내용: {content}")
        
        combined_text = "\n\n".join(financial_texts[:5])  # 상위 5개만 분석
        
        # 투자 성향별 맞춤 분석 프롬프트
        priorities = ', '.join(criteria.get('priorities', []))
        key_metrics = ', '.join(criteria.get('key_metrics', []))
        thresholds = criteria.get('thresholds', {})
        
        prompt = f"""당신은 금융 전문 애널리스트입니다. {stock_name}의 재무제표 데이터를 {investment_profile} 투자자 관점에서 분석해주세요.

=== 재무 데이터 ===
{combined_text}

=== 분석 기준 ===
투자 성향: {investment_profile}
우선순위: {priorities}
핵심 지표: {key_metrics}
기준값: {thresholds}

=== 분석 요청 ===
위 재무 데이터를 바탕으로 다음 형식으로 분석해주세요:

financial_score: [0-100점 (투자 매력도 점수)]
key_metrics: {{"ROE": "값", "PER": "값", "매출성장률": "값", "부채비율": "값"}}
strengths: ["강점1", "강점2", "강점3"]
weaknesses: ["약점1", "약점2"]
recommendation: [매우추천/추천/보통/비추천/매우비추천 중 하나]
analysis_summary: [2-3문장으로 핵심 요약]

=== 분석 가이드 ===
1. {investment_profile} 투자자가 중요하게 여기는 지표에 가중치 부여
2. 업종 특성 고려한 상대적 평가
3. 최근 트렌드와 성장성 종합 판단
4. 리스크 요인도 명확히 제시

응답은 반드시 위 형식을 정확히 따라주세요."""

        try:
            response = await self.llm.ainvoke(prompt)
            return self._parse_financial_analysis_response(
                response.content, 
                stock_name, 
                investment_profile
            )
        except Exception as e:
            print(f"⚠️ LLM 재무 분석 실패: {e}")
            return self._fallback_financial_analysis(stock_name, criteria)
    
    def _parse_financial_analysis_response(
        self,
        response_text: str,
        stock_name: str,
        investment_profile: str
    ) -> Dict[str, Any]:
        """LLM 재무 분석 응답 파싱"""
        
        result = {
            "financial_score": 50,
            "key_metrics": {},
            "strengths": [],
            "weaknesses": [],
            "recommendation": "보통",
            "analysis_summary": f"{stock_name}의 재무 분석 결과",
            "analysis_date": "2025-10-11"
        }
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'financial_score' in key:
                        try:
                            score = float(value)
                            result["financial_score"] = max(0, min(100, score))
                        except:
                            pass
                    elif 'key_metrics' in key:
                        # JSON 형태 파싱 시도
                        try:
                            if '{' in value and '}' in value:
                                # 간단한 dict 파싱
                                clean_value = value.replace('{', '').replace('}', '')
                                metrics = {}
                                for item in clean_value.split(','):
                                    if ':' in item:
                                        k, v = item.split(':', 1)
                                        metrics[k.strip().replace('"', '')] = v.strip().replace('"', '')
                                result["key_metrics"] = metrics
                        except:
                            pass
                    elif 'recommendation' in key:
                        if value in ["매우추천", "추천", "보통", "비추천", "매우비추천"]:
                            result["recommendation"] = value
                    elif 'analysis_summary' in key:
                        result["analysis_summary"] = value
                    elif any(factor_key in key for factor_key in ['strengths', 'weaknesses']):
                        factors = self._parse_array_field(value)
                        if 'strengths' in key:
                            result["strengths"] = factors[:3]
                        elif 'weaknesses' in key:
                            result["weaknesses"] = factors[:2]
            
        except Exception as e:
            print(f"⚠️ 재무 분석 응답 파싱 실패: {e}")
        
        return result
    
    def _parse_array_field(self, value: str) -> List[str]:
        """배열 형태 필드 파싱"""
        try:
            if '[' in value and ']' in value:
                clean_value = value.replace('[', '').replace(']', '').replace('"', '')
                items = [item.strip() for item in clean_value.split(',')]
                return [item for item in items if item]
            else:
                return [value] if value else []
        except:
            return [value] if value else []
    
    def _remove_duplicate_financial_data(
        self, 
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """중복 재무 데이터 제거"""
        
        seen_content = set()
        unique_results = []
        
        for result in results:
            content = result.get('text', result.get('content', ''))
            content_hash = hash(content[:200])  # 첫 200자로 중복 판단
            
            if content_hash not in seen_content and len(content) > 50:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _fallback_financial_analysis(
        self, 
        stock_name: str, 
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """폴백 재무 분석 (기본값)"""
        
        return {
            "financial_score": 50,
            "key_metrics": {"데이터": "부족"},
            "strengths": [f"{stock_name}의 상세 재무 데이터 분석 필요"],
            "weaknesses": ["재무제표 데이터 부족"],
            "recommendation": "보통",
            "analysis_summary": f"{stock_name}의 재무 데이터가 부족하여 추가 분석이 필요합니다.",
            "analysis_date": "2025-10-11"
        }
    
    def _get_default_financial_analysis(
        self, 
        stock_code: str, 
        stock_name: str
    ) -> Dict[str, Any]:
        """기본 재무 분석 (데이터 없을 때)"""
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "financial_score": 50,
            "key_metrics": {},
            "strengths": [],
            "weaknesses": ["재무 데이터 부족"],
            "recommendation": "보통",
            "analysis_summary": f"{stock_name}의 재무제표 분석을 위한 데이터가 부족합니다.",
            "data_sources": 0,
            "analysis_date": "2025-10-11"
        }
    
    async def get_multiple_stocks_analysis(
        self,
        stocks: List[Dict[str, str]],  # [{"code": "005930", "name": "삼성전자"}, ...]
        investment_profile: str
    ) -> Dict[str, Dict[str, Any]]:
        """여러 종목 동시 재무 분석"""
        
        print(f"📊 {len(stocks)}개 종목 재무 분석 시작 ({investment_profile})...")
        
        # 배치별 처리 (API 부하 방지)
        results = {}
        batch_size = 3
        
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i+batch_size]
            
            # 배치 내 동시 실행
            tasks = [
                self.get_financial_analysis(
                    stock["code"], 
                    stock["name"], 
                    investment_profile
                )
                for stock in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for stock, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"❌ {stock['name']} 재무 분석 실패: {result}")
                    results[stock["code"]] = self._get_default_financial_analysis(
                        stock["code"], 
                        stock["name"]
                    )
                else:
                    results[stock["code"]] = result
            
            # 배치 간 딜레이
            if i + batch_size < len(stocks):
                await asyncio.sleep(2)
        
        print(f"✅ 재무 분석 완료: {len(results)}개 종목")
        return results


# 전역 인스턴스
financial_data_service = FinancialDataService()
