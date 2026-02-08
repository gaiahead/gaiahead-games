#!/usr/bin/env python3
"""
듀얼 모멘텀 전략 - 금 포트폴리오 비중 계산

비교 자산:
1. 금: ACE KRX 금현물 (411060)
2. 미국채 10년: TIGER 미국채10년선물 (305080)
3. 나스닥: TIGER 미국나스닥100 (133690)

전략:
- 절대 모멘텀: 12개월 수익률 > 0
- 상대 모멘텀: 3개 자산 중 최고 수익률
- 비중 제안: 절대+상대 1위 = 100%, 절대만 = 50%, 절대 실패 = 0%
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

# ETF 정보
ASSETS = {
    "금": {"code": "411060", "name": "ACE KRX 금현물"},
    "미국채10년": {"code": "305080", "name": "TIGER 미국채10년선물"},
    "나스닥": {"code": "133690", "name": "TIGER 미국나스닥100"}
}

def get_price_data(code, days=365):
    """네이버 금융에서 과거 가격 데이터 수집"""
    url = f"https://finance.naver.com/item/sise_day.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    prices = []
    page = 1
    
    while len(prices) < days and page < 50:  # 최대 50페이지
        try:
            response = requests.get(f"{url}&page={page}", headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 테이블 파싱
            table = soup.find('table', {'class': 'type2'})
            if not table:
                break
                
            rows = table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    try:
                        date_str = cols[0].text.strip()
                        close_str = cols[1].text.strip().replace(',', '')
                        
                        if date_str and close_str:
                            date = datetime.strptime(date_str, '%Y.%m.%d')
                            close = int(close_str)
                            prices.append({'date': date, 'close': close})
                    except:
                        continue
            
            page += 1
            
        except Exception as e:
            print(f"  ⚠️ 페이지 {page} 수집 실패: {e}")
            break
    
    # 날짜 순 정렬 (오래된 순)
    prices.sort(key=lambda x: x['date'])
    return prices

def calculate_momentum(prices):
    """12개월 수익률 계산"""
    if len(prices) < 2:
        return None
    
    # 최신가 vs 12개월 전
    latest = prices[-1]['close']
    year_ago = prices[0]['close']
    
    return_pct = ((latest - year_ago) / year_ago) * 100
    return return_pct

def dual_momentum_strategy():
    """듀얼 모멘텀 전략 실행"""
    print("=" * 60)
    print("📊 듀얼 모멘텀 전략 - 금 포트폴리오 비중 계산")
    print("=" * 60)
    print()
    
    results = {}
    
    # 1. 각 자산별 데이터 수집 및 수익률 계산
    print("🔍 데이터 수집 중...\n")
    
    for asset_key, asset_info in ASSETS.items():
        print(f"  {asset_info['name']} ({asset_info['code']})")
        prices = get_price_data(asset_info['code'], days=365)
        
        if len(prices) < 200:
            print(f"    ⚠️ 데이터 부족: {len(prices)}일")
            continue
        
        momentum = calculate_momentum(prices)
        
        results[asset_key] = {
            "name": asset_info['name'],
            "code": asset_info['code'],
            "latest_price": prices[-1]['close'],
            "year_ago_price": prices[0]['close'],
            "momentum_12m": momentum,
            "data_points": len(prices)
        }
        
        print(f"    ✅ 12개월 수익률: {momentum:+.2f}% ({len(prices)}일 데이터)")
        print()
    
    if not results:
        print("❌ 데이터 수집 실패")
        return
    
    # 2. 절대 모멘텀 체크 (금)
    print("-" * 60)
    print("📈 듀얼 모멘텀 분석\n")
    
    gold = results.get("금")
    if not gold:
        print("❌ 금 데이터 없음")
        return
    
    absolute_momentum = gold['momentum_12m'] > 0
    print(f"1️⃣ 절대 모멘텀 (금 12개월 수익률 > 0)")
    print(f"   금: {gold['momentum_12m']:+.2f}%")
    print(f"   → {'✅ 통과' if absolute_momentum else '❌ 실패'}")
    print()
    
    # 3. 상대 모멘텀 체크 (순위)
    print(f"2️⃣ 상대 모멘텀 (3개 자산 순위)\n")
    
    sorted_assets = sorted(results.items(), key=lambda x: x[1]['momentum_12m'], reverse=True)
    
    for rank, (key, data) in enumerate(sorted_assets, 1):
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
        print(f"   {emoji} {rank}위: {data['name']}")
        print(f"      12개월 수익률: {data['momentum_12m']:+.2f}%")
        print()
    
    gold_rank = next(i for i, (k, _) in enumerate(sorted_assets, 1) if k == "금")
    
    # 4. 비중 제안
    print("-" * 60)
    print("💰 포트폴리오 비중 제안\n")
    
    if not absolute_momentum:
        allocation = 0
        reason = "절대 모멘텀 실패 (12개월 수익률 < 0)"
    elif gold_rank == 1:
        allocation = 100
        reason = "절대 모멘텀 통과 + 상대 모멘텀 1위"
    elif gold_rank == 2:
        allocation = 50
        reason = "절대 모멘텀 통과 + 상대 모멘텀 2위"
    else:
        allocation = 25
        reason = "절대 모멘텀 통과 + 상대 모멘텀 3위"
    
    print(f"   금 비중: {allocation}%")
    print(f"   근거: {reason}")
    print()
    
    if allocation < 100:
        print(f"   나머지 {100 - allocation}%:")
        if not absolute_momentum:
            print(f"      → 현금 or 미국 단기채")
        else:
            best = sorted_assets[0]
            if best[0] != "금":
                print(f"      → {best[1]['name']} ({best[1]['momentum_12m']:+.2f}%)")
    print()
    
    # 5. JSON 결과 저장
    output = {
        "timestamp": datetime.now().isoformat(),
        "assets": results,
        "gold_absolute_momentum": absolute_momentum,
        "gold_rank": gold_rank,
        "allocation": allocation,
        "reason": reason
    }
    
    output_path = "/home/gaiahead/.openclaw/workspace/memory/dual_momentum_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"📁 결과 저장: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    dual_momentum_strategy()
