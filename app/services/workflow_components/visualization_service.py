"""
시각화 서비스 - 캔들스틱 + 거래량 통합 차트 생성
"""

import matplotlib
matplotlib.use('Agg')  # GUI 없이 차트 생성
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io
import base64
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

# 한글 폰트 설정 (macOS)
try:
    plt.rcParams['font.family'] = 'AppleGothic'
except:
    # 폰트가 없으면 기본 폰트 사용
    pass
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지


class VisualizationService:
    """캔들스틱 + 거래량 통합 차트 생성 서비스"""
    
    def __init__(self):
        pass
    
    def determine_chart_type(self, query: str, data: Dict[str, Any]) -> str:
        """
        모든 시각화 요청을 캔들스틱 + 거래량 통합 차트로 처리
        
        Args:
            query: 사용자 질문
            data: 금융 데이터
            
        Returns:
            str: 차트 타입 (항상 'candlestick_volume')
        """
        # 모든 시각화 요청을 캔들스틱 + 거래량 통합 차트로 처리
        return 'candlestick_volume'
    
    def create_chart(self, chart_type: str, data: Dict[str, Any], **kwargs) -> str:
        """
        차트 생성 및 base64 인코딩
        
        Args:
            chart_type: 차트 타입
            data: 차트 데이터
            **kwargs: 추가 파라미터
            
        Returns:
            str: base64 인코딩된 이미지
        """
        try:
            # 항상 캔들스틱 + 거래량 통합 차트 생성
            return self._create_candlestick_volume_chart(data, **kwargs)
            
        except Exception as e:
            print(f"❌ 차트 생성 실패: {e}")
            return self._create_error_chart(str(e))
    
    def _create_candlestick_volume_chart(self, data: Dict[str, Any], **kwargs) -> str:
        """캔들스틱 + 거래량 통합 차트 생성"""
        symbol = data.get('symbol', 'Unknown')
        company_name = data.get('company_name', 'Unknown')
        period = kwargs.get('period', '1mo')
        
        # yfinance에서 히스토리 데이터 가져오기
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        # None 체크 추가
        if hist is None or hist.empty:
            return self._create_error_chart(f"{symbol} 데이터를 찾을 수 없습니다.")
        
        # 캔들스틱 + 거래량 통합 차트
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                       gridspec_kw={'height_ratios': [2, 1]})
        
        # 상단: 캔들스틱 차트
        for idx, (date, row) in enumerate(hist.iterrows()):
            color = 'red' if row['Close'] >= row['Open'] else 'blue'
            
            # 몸통
            ax1.plot([idx, idx], [row['Open'], row['Close']], 
                     color=color, linewidth=8, solid_capstyle='round')
            
            # 그림자
            ax1.plot([idx, idx], [row['Low'], row['High']], 
                     color=color, linewidth=1)
        
        ax1.set_title(f'{company_name} ({symbol}) 캔들스틱 & 거래량 분석', fontsize=16, fontweight='bold')
        ax1.set_ylabel('주가 ($)')
        ax1.grid(True, alpha=0.3)
        
        # X축 날짜 레이블 (상단만)
        step = max(1, len(hist) // 10)
        ax1.set_xticks(range(0, len(hist), step))
        ax1.set_xticklabels([hist.index[i].strftime('%m/%d') for i in range(0, len(hist), step)], 
                            rotation=45)
        
        # 하단: 거래량 차트
        colors = ['red' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else 'blue' 
                 for i in range(len(hist))]
        ax2.bar(hist.index, hist['Volume'], color=colors, alpha=0.6)
        ax2.set_xlabel('날짜')
        ax2.set_ylabel('거래량')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 평균 거래량 표시
        avg_volume = hist['Volume'].mean()
        ax2.axhline(y=avg_volume, color='green', linestyle='--', 
                   label=f'평균: {avg_volume:,.0f}', linewidth=2)
        ax2.legend()
        
        plt.tight_layout()
        
        # test: 차트를 직접 표시 (test_agent.py 실행 시)
        plt.show()
        
        return self._fig_to_base64(fig)
    
    def _create_error_chart(self, error_message: str) -> str:
        """에러 메시지 차트"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'❌ 차트 생성 실패\n\n{error_message}',
               ha='center', va='center', fontsize=14, color='red',
               transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.axis('off')
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """matplotlib figure를 base64로 인코딩"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64


# 전역 시각화 서비스 인스턴스
visualization_service = VisualizationService()