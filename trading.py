import requests
import json
import datetime
import time
import keyring
import selection
import os

APP_KEY = keyring.get_password('real_app_key', 'occam123')
APP_SECRET = keyring.get_password('real_app_secret', 'occam123')
URL_BASE = "https://openapi.koreainvestment.com:9443"  # 실전 투자
CANO = keyring.get_password('CANO', 'occam123')
ACNT_PRDT_CD = '01'


def get_access_token():
    """토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        'content-Type': 'application/json',
        'appKey': APP_KEY,
        'appSecret': APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey


def get_current_price(code="005930"): # 주식 현재가 시세
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010100"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr']), float(res.json()['output']['prdy_vrss_vol_rate'])
    # Return: 주식 현재가, 전일 대비 거래량 비율


def get_target_price(code="005930"):
    """전날 종가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010400"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_org_adj_prc": "1",
        "fid_period_div_code": "D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
    target_price = stck_clpr
    return target_price


def get_stock_5d_before():
    def get_stock_before(date):
        PATH = "uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        URL = f"{URL_BASE}/{PATH}"
        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {ACCESS_TOKEN}",
                   "appKey": APP_KEY,
                   "appSecret": APP_SECRET,
                   "tr_id": "TTTC8001R",  # 실전 투자 "TTTC8001R", 모의투자 "VTTC8001R"
                   "custtype": "P",
                   }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "INQR_STRT_DT": date,
            "INQR_END_DT": date,
            "SLL_BUY_DVSN_CD": "02",  # 00:전체, 01:매도, 02:매수
            "INQR_DVSN": "01",  # 00: 역순
            "PDNO": "",
            "CCLD_DVSN": "01",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "01",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        stock_dict = res.json()['output1']
        return stock_dict

    prev = 7
    while prev < 15:
        t_previous_5d = datetime.datetime.now().date() - datetime.timedelta(days=prev)
        t_previous_5d = t_previous_5d.strftime("%Y%m%d")
        bought_previous_5d_dict = get_stock_before(t_previous_5d)
        if len(bought_previous_5d_dict) > 0:
            break
        else:
            prev += 1
    sell_list_5d_over = []
    for stock in bought_previous_5d_dict:
        sell_list_5d_over.append(stock['pdno'])
    sell_list_5d_over = list(set(sell_list_5d_over))
    return sell_list_5d_over


def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8434R",  # 실전 투자 "TTTC8434R" 모의투자 "VTTC8434R"
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    print(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = [stock['hldg_qty'], stock['ord_psbl_qty'], stock['evlu_pfls_rt']]  # 0: 보유 수량, 1: 평가수익율
            print(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    print(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    print(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    print(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    print(f"=================")
    return stock_dict


def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8908R",  # 실전 투자 : "TTTC8908R" 모의투자 "VTTC8908R"
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    print(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)


def buy(code="005930", qty="1", buy_price="0"):
    """주식 시장가 매수"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": qty,
        "ORD_UNPR": buy_price,
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0802U",  # 실전 투자 : "TTTC0802U" 모의투자 'VTTC0802U'
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        print(f"[매수 성공]{str(res.json())}")
        return True
    else:
        print(f"[매수 실패]{str(res.json())}")
        return False


def sell(code="005930", qty="1", sell_price="0", sell_type="00"):
    """주식 시장가 매도"""

    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": sell_type,
        "ORD_QTY": qty,
        "ORD_UNPR": sell_price,
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0801U",  # 실전 투자 : TTTC0801U "VTTC0801U"
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        print(f"[매도 성공]{str(res.json())}")
        return True
    else:
        print(f"[매도 실패]{str(res.json())}")
        return False


ACCESS_TOKEN = get_access_token()


def ho(x):
    if x >= 500000:
        return 1000
    elif x >= 100000:
        return 500
    elif x >= 50000:
        return 100
    elif x >= 10000:
        return 50
    elif x >= 5000:
        return 10
    elif x > 1000:
        return 5
    else:
        return 1

def auto_trading():  # 매수 희망 종목 리스트
    print("===국내 주식 자동매매 프로그램을 시작합니다===")
    # 자동매매 시작
    try:
        flag = 0
        while True:

            t_now = datetime.datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=12, minute=7, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=19, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            today = datetime.datetime.today().weekday()

            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                print("주말이므로 프로그램을 종료합니다.")
                break

            if t_9 < t_now < t_sell:  # AM 09:00 ~ PM 03:19

                # 장 중 매수 코드
                if (t_start < t_now) and flag == 0:
                    # 종목 선정
                    today = t_now.strftime('%Y-%m-%d')  # 오늘
                    select_tops = selection.select_stocks(today).sort_values(by='yhat', ascending=False).head(6)

                    symbol_list = list(select_tops.index)
                    print(symbol_list)
                    flag = 1

                    bought_list = []  # 매수 완료된 종목 리스트
                    total_cash = get_balance()  # 보유 현금 조회
                    stock_dict = get_stock_balance()  # 보유 주식 조회

                    for sym in stock_dict.keys():
                        bought_list.append(sym)

                    symbol_list = list(set(symbol_list) - set(bought_list))  # 기 매수 종목 제거

                    if len(symbol_list) > 0:
                        buy_percent = 1 / len(symbol_list)  # 종목당 매수 금액 비율
                    else:
                        buy_percent = 0  # 종목당 매수 금액 비율

                    buy_amount = total_cash * 0.5 * buy_percent  # 종목별 주문 금액 계산

                    # 매수 코드
                    for sym in symbol_list:

                        target_price = get_target_price(sym)  # 전날 종가, Get from Input dictionary
                        current_price, volume_rate = get_current_price(sym)

                        t_progress = (t_now - t_9) / (t_exit - t_9)

                        c1 = (target_price < current_price)
                        c2 = (float(volume_rate / t_progress) > 1.0)
                        print(c1, c2)
                        print(
                            f'종목: {sym}, 현재가: {current_price}, 전일종가: {target_price}, 거래량지표: {float(volume_rate / t_progress):5.1f}')
                        if c1 and c2:  # Max: 5% 상승 가격, Min: 전날 종가

                            buy_qty = 0  # 매수할 수량 초기화
                            buy_qty = int(buy_amount // current_price)
                            if (buy_qty > 0):

                                print(f"{sym} 목표가 달성({target_price} < {current_price}) 매수를 시도합니다.")
                                buy_price = float(current_price) - ho(float(current_price))
                                print(sym, str(int(buy_qty)), str(int(buy_price)))
                                result = buy(sym, str(int(buy_qty)), str(int(buy_price)))
                                if result:
                                    bought_list.append(sym)  # 매수 종목


                        time.sleep(1)

                # 장 중 매도 코드 (지정가)
                balance_dict = get_stock_balance()

                for sym, qty_rt in balance_dict.items():  # qty_rt / [0]: 보유수량, [1] 주문가능 수량 [2]: rt(평가수익율)

                    print(f'{sym} 현재 수익율: {float(qty_rt[2]): 5.2f}')
                    current_price, volume_rate = get_current_price(sym)
                    sell_price = float(current_price) + ho(float(current_price))  # 한 호가 높여 매도 주문

                    if float(qty_rt[2]) > 1.5 or float(qty_rt[2]) < -1.5:  # 익절 라인은 dynamic 하게 바꿀 수 있다 (단위 %)

                        print(sym, str(qty_rt[1]), str(int(sell_price))) # 매도 주문 인자 정보
                        if float(qty_rt[1])!=0:
                            # sell(sym, str(qty_rt[1]), str(int(sell_price)), "00") # "00 지정가 매도
                            sell(sym, str(qty_rt[1]), "0", "01") # "01 시장가 메도

                time.sleep(1)

                if t_now.minute == 30 and t_now.second <= 5:  # 매 30분 마다 창 지움
                    os.system('cls')
                    time.sleep(1)

            # PM 03:15 ~ PM 03:20 : 5th Day 를 맞이한 종목들 일괄 매도
            if t_sell < t_now < t_exit:

                sell_list_5d_over = get_stock_5d_before()
                stock_dict = get_stock_balance()

                sell_list = list(set(stock_dict.keys()) & set(sell_list_5d_over))  # 보유종목 중 5일이상 된 종목
                for sym in sell_list:
                    sell(sym, stock_dict['sym'][0])  # 보유종목 중 5일이상 된 종목 전량 매도     

                time.sleep(1)

            # PM 03:20 ~ :프로그램 종료
            if t_exit < t_now:
                print("프로그램을 종료합니다.")
                break


    except Exception as e:
        print(f"[오류 발생]{e}")
        time.sleep(1)
