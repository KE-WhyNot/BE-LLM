import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.intent_analysis_service import IntentAnalysisService
from app.services.rag_service import rag_service
from app.services.monitoring_service import monitoring_service
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.utils.stock_utils import extract_company_name, get_stock_symbol
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

# 토크나이저 병렬 처리 비활성화
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from app.services.rag_service import rag_service
from app.services.monitoring_service import monitoring_service
from app.schemas.chat_schema import ChatRequest, ChatResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

class EnhancedFinancialChatbotService:
    """향상된 금융 전문가 챗봇 서비스"""
    
    def __init__(self):
        self.intent_analyzer = IntentAnalysisService()
        self.rag_service = rag_service
        self.monitoring_service = monitoring_service
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # financial_agent.py와 동일한 모델 사용
            temperature=settings.gemini_temperature,
            google_api_key=settings.google_api_key,
            max_output_tokens=settings.gemini_max_tokens,
            convert_system_message_to_human=True
        )
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """개선된 채팅 요청 처리 파이프라인"""
        try:
            start_time = datetime.now()
            
            # 1. 의도 분석
            intent_analysis = self.intent_analyzer.analyze_intent(request.message)
            
            # 2. 컨텍스트 수집
            context = await self._gather_context(request.message, intent_analysis)
            
            # 3. Gemini를 통한 응답 생성
            response = await self._generate_response(request.message, context, intent_analysis)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 모니터링 로그
            self.monitoring_service.trace_query(
                request.message,
                response["answer"],
                {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "processing_time": processing_time,
                    "intent": intent_analysis["intent"],
                    "confidence": intent_analysis["confidence"],
                    "realtime_data_used": context["realtime_data"] is not None
                }
            )
            
            return ChatResponse(
                reply_text=response["answer"],
                action_type=intent_analysis["intent"],
                action_data=response["supporting_data"]
            )
            
        except Exception as e:
            error_msg = f"처리 중 오류가 발생했습니다: {str(e)}"
            self.monitoring_service.log_error(
                "enhanced_chatbot_error",
                str(e),
                {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "message": request.message
                }
            )
            return self._create_error_response(error_msg)
    
    async def _gather_context(self, query: str, intent_analysis: dict) -> dict:
        """의도에 따른 컨텍스트 수집"""
        context = {
            "documents": [],
            "realtime_data": None,
            "intent": intent_analysis
        }
        
        try:
            # 1. RAG를 통한 관련 문서 검색
            try:
                # 벡터 스토어에서 Document 리스트 가져오기
                if hasattr(self.rag_service, 'search_relevant_documents'):
                    docs = self.rag_service.search_relevant_documents(query, k=3)
                    if isinstance(docs, list):
                        context["documents"] = docs

                # 추가적으로 상세 컨텍스트 텍스트 획득
                if hasattr(self.rag_service, 'get_context_for_query'):
                    try:
                        context_text = self.rag_service.get_context_for_query(query)
                        context["context_text"] = context_text
                    except Exception:
                        context["context_text"] = None
            except Exception as e:
                print(f"문서 검색 중 오류: {e}")
            
            # 2. 실시간 데이터가 필요한 경우 수집
            if intent_analysis.get("requires_realtime") or intent_analysis.get("intent") == "stock_info":
                if intent_analysis.get("intent") == "stock_info":
                    company_name = extract_company_name(query)
                    symbol = get_stock_symbol(company_name)
                    if symbol:
                        # rag_service.get_financial_data는 동기 함수입니다
                        data = self.rag_service.get_financial_data(symbol)
                            
                        if isinstance(data, dict) and "error" not in data:
                            context["realtime_data"] = data
                            print(f"✅ {company_name}({symbol}) 주가 데이터 수집 완료")
                        else:
                            error_msg = data.get('error', '알 수 없는 오류') if isinstance(data, dict) else str(data)
                            print(f"⚠️ {company_name}({symbol}) 주가 데이터 수집 실패: {error_msg}")
                elif intent_analysis.get("intent") == "market_analysis":
                    # rag_service.get_market_data는 동기 함수입니다
                    data = self.rag_service.get_market_data()
                        
                    if isinstance(data, dict) and "error" not in data:
                        context["realtime_data"] = data
                        print("✅ 시장 데이터 수집 완료")
                    else:
                        error_msg = data.get('error', '알 수 없는 오류') if isinstance(data, dict) else str(data)
                        print(f"⚠️ 시장 데이터 수집 실패: {error_msg}")
        except Exception as e:
            print(f"컨텍스트 수집 중 오류 발생: {str(e)}")
            # 오류가 발생해도 기본 컨텍스트는 유지
            context["error"] = str(e)
        
        return context
    
    async def _generate_response(self, query: str, context: dict, intent_analysis: dict) -> dict:
        """Gemini를 사용한 응답 생성"""
        try:
            # 뉴스 요청인 경우 뉴스 검색 및 분석
            if intent_analysis.get("intent") == "news_query":
                try:
                    # 뉴스 검색
                    news_list = self.rag_service.get_financial_news(query, max_results=5)
                    
                    if not news_list:
                        return {
                            "answer": f"'{query}' 관련 뉴스를 찾을 수 없습니다.",
                            "supporting_data": {
                                "intent": "news_query",
                                "confidence": intent_analysis.get("confidence", 0.0),
                                "error": "no_news_found"
                            }
                        }
                    
                    # 뉴스 요약 및 분석
                    news_summary = "📰 최신 뉴스 요약:\n\n"
                    for i, news in enumerate(news_list, 1):
                        news_summary += f"{i}. **{news['title']}**\n"
                        news_summary += f"   📝 {news['summary']}\n"
                        news_summary += f"   📅 {news['published']}\n\n"
                    
                    # 뉴스 분석 추가
                    news_summary += "🔍 **뉴스 분석 및 시장 전망:**\n"
                    news_summary += "• 최근 뉴스들을 종합적으로 분석하여 시장 동향을 파악하세요.\n"
                    news_summary += "• 긍정적 뉴스는 주가 상승 요인, 부정적 뉴스는 하락 요인이 될 수 있습니다.\n"
                    news_summary += "• 단일 뉴스보다는 여러 뉴스를 종합하여 판단하는 것이 중요합니다.\n"
                    
                    return {
                        "answer": news_summary,
                        "supporting_data": {
                            "intent": "news_query",
                            "confidence": intent_analysis.get("confidence", 0.0),
                            "news_count": len(news_list),
                            "sources": [news.get('url', '') for news in news_list]
                        }
                    }
                except Exception as e:
                    return {
                        "answer": f"뉴스 검색 중 오류가 발생했습니다: {str(e)}",
                        "supporting_data": {
                            "intent": "news_query",
                            "confidence": intent_analysis.get("confidence", 0.0),
                            "error": str(e)
                        }
                    }
            
            # 주식 정보 요청인 경우 직접 처리
            elif intent_analysis.get("intent") == "stock_info":
                company_name = extract_company_name(query)
                symbol = get_stock_symbol(company_name)
                
                if not symbol:
                    return {
                        "answer": f"죄송합니다. '{company_name}'에 대한 주식 심볼을 찾을 수 없습니다.",
                        "supporting_data": {
                            "intent": "stock_info",
                            "confidence": intent_analysis.get("confidence", 0.0),
                            "error": "stock_symbol_not_found"
                        }
                    }
                
                try:
                    # 이미 컨텍스트에 있는 데이터 사용
                    if context.get("realtime_data"):
                        stock_data = context["realtime_data"]
                    else:
                        # 없으면 새로 조회
                        # rag_service.get_financial_data는 동기 함수입니다
                        stock_data = self.rag_service.get_financial_data(symbol)
                
                    if isinstance(stock_data, dict) and "error" not in stock_data:
                        response_text = f"""
{stock_data['company_name']} ({symbol}) 현재 주가 정보:
- 현재가: {stock_data.get('current_price', 'N/A'):,}원
- 전일대비: {stock_data.get('price_change', 0):+,}원 ({stock_data.get('price_change_percent', 0):+.2f}%)
- 거래량: {stock_data.get('volume', 'N/A'):,}주
- 고가: {stock_data.get('high', 'N/A'):,}원
- 저가: {stock_data.get('low', 'N/A'):,}원
- 시가: {stock_data.get('open', 'N/A'):,}원
                        """
                    else:
                        error_msg = stock_data.get('error', '알 수 없는 오류') if isinstance(stock_data, dict) else str(stock_data)
                        response_text = f"죄송합니다. 주가 데이터 조회 중 오류가 발생했습니다: {error_msg}"
                    
                    return {
                        "answer": response_text,
                        "supporting_data": {
                            "intent": "stock_info",
                            "confidence": intent_analysis.get("confidence", 0.0),
                            "realtime_data": stock_data if isinstance(stock_data, dict) else None
                        }
                    }
                except Exception as e:
                    return {
                        "answer": f"죄송합니다. 주가 데이터 처리 중 오류가 발생했습니다: {str(e)}",
                        "supporting_data": {
                            "intent": "stock_info",
                            "confidence": intent_analysis.get("confidence", 0.0),
                            "error": str(e)
                        }
                    }
            
            # 다른 의도의 경우 Gemini 사용
            prompt = self._create_prompt(query, context, intent_analysis)
            
            response = None
            try:
                print(f"[DEBUG] Gemini API 호출 시작...")
                print(f"[DEBUG] 프롬프트 길이: {len(prompt)}")
                
                # 직접 Gemini API 호출 (LangChain 대신)
                try:
                    import google.generativeai as genai
                    import os
                    
                    # Google API 키 설정
                    api_key = os.getenv('GOOGLE_API_KEY')
                    if not api_key:
                        raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
                    
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    # 직접 API 호출
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: model.generate_content(prompt)
                    )
                    
                    print(f"[DEBUG] Gemini API 호출 성공!")
                    print(f"[DEBUG] Gemini response type: {type(response)}")
                    print(f"[DEBUG] Gemini response: {response}")
                except Exception as api_error:
                    print(f"[DEBUG] Gemini API 호출 실패: {api_error}")
                    print(f"[DEBUG] API 오류 타입: {type(api_error)}")
                    raise api_error

                # Gemini 응답 처리 - 직접 API 응답 형식
                answer = None
                
                # 직접 Gemini API 응답 처리
                if hasattr(response, 'text'):
                    answer = response.text
                elif hasattr(response, 'parts') and response.parts:
                    # parts 배열에서 텍스트 추출
                    text_parts = []
                    for part in response.parts:
                        if hasattr(part, 'text'):
                            text_parts.append(part.text)
                    answer = ' '.join(text_parts)
                else:
                    # 폴백: 문자열로 변환
                    answer = str(response)

                if not answer:
                    raise ValueError(f"응답 처리 실패: unexpected response shape {type(response)}")

                if isinstance(answer, bytes):
                    answer = answer.decode('utf-8', errors='ignore')

                answer = str(answer).strip()
            except Exception as e:
                print(f"Gemini 응답 생성 중 오류: {str(e)}")
                print(f"오류 타입: {type(e)}")
                if response is not None:
                    print(f"응답 타입: {type(response)}")
                    print(f"응답 내용: {response}")
                else:
                    print("응답이 None입니다.")
                # 남은 예외는 호출자에게 전달하여 로깅되도록 함
                raise
            
            # 문서 소스 추출
            sources = []
            if context.get("documents"):
                for doc in context["documents"]:
                    try:
                        if isinstance(doc, dict) and doc.get("source"):
                            sources.append(doc["source"])
                        elif hasattr(doc, 'metadata') and doc.metadata.get("source"):
                            sources.append(doc.metadata["source"])
                        elif hasattr(doc, 'page_content'):
                            # 소스가 없는 경우 내용의 일부를 ID로 사용
                            content_preview = doc.page_content[:50] + "..."
                            sources.append(f"Content: {content_preview}")
                    except Exception as e:
                        print(f"소스 추출 중 오류: {str(e)}")
                        continue
            
            return {
                "answer": answer,
                "supporting_data": {
                    "intent": intent_analysis.get("intent", "unknown"),
                    "confidence": intent_analysis.get("confidence", 0.0),
                    "sources": sources,
                    "realtime_data_used": bool(context.get("realtime_data"))
                }
            }
        except Exception as e:
            print(f"응답 생성 중 오류 발생: {str(e)}")
            return {
                "answer": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "supporting_data": {
                    "intent": intent_analysis.get("intent", "unknown"),
                    "confidence": intent_analysis.get("confidence", 0.0),
                    "error": str(e)
                }
            }
    
    def _create_prompt(self, query: str, context: dict, intent_analysis: dict) -> str:
        """컨텍스트를 포함한 프롬프트 생성"""
        # 문서 포맷팅
        docs_text = ""
        if context.get('documents'):
            try:
                docs_text = "\n".join([f"- {doc.page_content}" for doc in context['documents'] if hasattr(doc, 'page_content')])
            except:
                docs_text = str(context['documents'])
        
        # 실시간 데이터 포맷팅
        realtime_data = context.get('realtime_data', '')
        if realtime_data:
            if isinstance(realtime_data, dict):
                realtime_data = json.dumps(realtime_data, ensure_ascii=False, indent=2)
            else:
                realtime_data = str(realtime_data)
        
        prompt = f"""당신은 전문 금융 어드바이저입니다. 다음 정보를 바탕으로 사용자의 질문에 답변해주세요.

사용자 질문: {query}

의도 분석: {intent_analysis.get('intent')} (신뢰도: {intent_analysis.get('confidence', 0):.2f})

관련 문서:
{docs_text}

{'실시간 데이터:' if realtime_data else ''}
{realtime_data if realtime_data else ''}

다음 형식으로 답변해주세요:
1. 핵심 답변
2. 근거 데이터
3. 추가 조언 (있는 경우)
"""
        return prompt
    
    def _format_documents(self, documents: list) -> str:
        """문서 포맷팅"""
        if not documents:
            return "관련 문서가 없습니다."
        
        formatted = []
        for i, doc in enumerate(documents, 1):
            formatted.append(f"{i}. {doc['content']} (출처: {doc['source']})")
        
        return "\n".join(formatted)
    
    def _create_error_response(self, error_msg: str) -> ChatResponse:
        """에러 응답 생성"""
        return ChatResponse(
            reply_text=error_msg,
            action_type="error",
            action_data={"error": error_msg}
        )
