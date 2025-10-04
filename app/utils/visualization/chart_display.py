#!/usr/bin/env python3
"""
실시간 차트 표시 도구
사용법: python3 show_charts.py
"""

import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def show_stock_charts(symbol='AAPL', company_name='Apple Inc.'):
    """주식 차트들을 표시"""
    
    print(f'🎨 {company_name} ({symbol}) 차트 생성 중...')
    print('=' * 60)
    
    # 데이터 가져오기
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period='1mo')
    info = ticker.info
    
    current_price = hist['Close'].iloc[-1]
    print(f'📊 {company_name} - ${current_price:.2f}')
    
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
    
    ax1.set_title(f'{company_name} 캔들스틱 & 거래량 분석', fontsize=16, fontweight='bold')
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
    plt.show()
    
    print('✅ 캔들스틱 & 거래량 통합 차트 표시 완료!')
    print(f'\n🎉 {company_name}의 차트가 성공적으로 표시되었습니다!')

def main():
    """메인 함수"""
    print('🎨 AI Agent 시각화 차트 도구')
    print('=' * 50)
    
    # 기본 Apple 차트
    show_stock_charts('AAPL', 'Apple Inc.')
    
    print('\n' + '=' * 50)
    print('💡 다른 종목도 테스트해보세요!')
    print('   예: show_stock_charts("MSFT", "Microsoft")')
    print('   예: show_stock_charts("GOOGL", "Google")')

if __name__ == '__main__':
    main()
