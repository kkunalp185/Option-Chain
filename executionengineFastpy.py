# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 14:57:01 2022

@author: niraj.munot
"""

import pandas as pd 
import requests 
import datetime
import numpy as np
from typing import Literal
import time

desired_width = 320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 12)

_seg = Literal['cash', "fno"]
    
class ExecutionEngine():
    def __init__(self): 
        super().__init__()
        self.url = ""
        self.endpoints = {
                           "multitouchline" : "https://finx.choiceindia.com/api/" + "OpenAPI/MultipleTouchline",
                           "fundsview" :  "https://finx.choiceindia.com/api/" + "OpenAPI/FundsView",
                           "chartapi" : "https://finx.choiceindia.com/api/" + "cm/Graph/GetChartHistory"
                          }
        
        self.timeout = 5
        self.reqsession = requests.Session()
        self.diff_delta = (datetime.datetime(1980, 1, 1, 0, 0, 0) - datetime.datetime(1970, 1, 1, 0, 0, 0)).total_seconds()
        curdate = datetime.datetime.now().date()
        self.curdate = datetime.datetime.combine(curdate, datetime.time(9,15))
        self.starttime = datetime.datetime.combine(datetime.datetime.now().date(),datetime.time(9,15)).timestamp()
        self.endtime = datetime.datetime.combine(datetime.datetime.now().date(),datetime.time(15,30)).timestamp()
        self.headers = {
            "VendorId" : "",
            "VendorKey" : "",
            }    
        self.userid_fordata = ""
        self.sessionid_fordata = ""
            
# =============================================================================
#     def multitouchline(self, tokens):
#         """
#         Parameters
#         ----------
#         tokens : list
#             Give List of tokens.
#         """
#         stn = ""
#         for i in tokens: 
#             segid = self.tokensdf[self.tokensdf['Token'] == int(i)].iloc[0]["Segment"]
#             if tokens.index(i) == len(tokens) - 1 : 
#                 stn = stn + str(segid) + "@" + str(i)
#             else :
#                 stn = stn + str(segid) + "@" + str(i) + ","
#         
#         body = {"MultipleSegToken": stn}
#         return self._requestCHARTAPI("POST", self.endpoints['multitouchline'], body = body)
#     
# =============================================================================
    
    def _get_date_tm(self,date):
        d1 = datetime.datetime(1980, 1, 1, 0, 0, 0)
        dt = datetime.datetime.combine(date, datetime.time(hour=0, minute=0))
        return int((dt-d1).total_seconds())
    
    def _fetchdata(self, token, segment, startdate, enddate, interval = 1):
        # NSECash = 1
        # NSEFNO = 2
        # BSECash = 3
        # MCXNFO = 5
        # MCXSpot = 6
        # NCDEXNFO = 7
        # NCDEXSpot = 9
        # CDSNFO = 13
        # CDSSpot = 14
        startdate = self._get_date_tm(startdate)
        enddate = self._get_date_tm(enddate)
        # segment = int(self.tokensdf[self.tokensdf['Token'] == int(token)].iloc[0]["Segment"])
        segment = 1 if segment == "cash" else 2 if segment == "fno" else None
        body = {
        "UseirId":self.userid_fordata,
        "SessionId":self.sessionid_fordata,
        "SegmentId":segment,
        "Token":token,
        "FromDate":str(startdate),
        "ToDate":str(enddate),
        "Interval":str(interval)
           }
        return self._requestCHARTAPI("POST",self.endpoints["chartapi"], body = body)
    
    def _processdataCHARTAPI(self, data):
        #print(data)
        tmplst = [i.split(',') for i in data['lstChartHistory']]
        #print(tmplst)
        df = pd.DataFrame(tmplst, columns = ['Datetime', "Open", "High", "Low", "Close", "Volume", "OpenInterest"])
        df = df.apply(pd.to_numeric)
        # df[['Open', "High", "Low", "Close", "Volume", "OpenInterest"]] = df[['Open', "High", "Low", "Close", "Volume", "OpenInterest"]] / 100.0
        df[['Open', "High", "Low", "Close"]] = df[['Open', "High", "Low", "Close"]] / 100.0
        df['Datetime'] = pd.to_datetime(df['Datetime']+self.diff_delta, unit = "s")
        df['Datetime'] = df['Datetime'].apply(lambda x :x.replace(second=0))
        df = df.set_index("Datetime")
        return df
    
    def datafrom_CHARTAPI(self, token, startdate, enddate, segment: _seg = "fno", interval = 1):
        data = self._fetchdata(token, segment, startdate, enddate, interval = interval)
        return self._processdataCHARTAPI(data)
    
    def _requestCHARTAPI(self, method, url, body = None, is_headers = True): 
        try :  
            if is_headers :
                resp = self.reqsession.request(method, url, json = body, headers = self.headers, timeout= self.timeout) 
            
            if not is_headers :
                resp = self.reqsession.request(method, url, json = body, timeout = self.timeout)
            
            if resp.status_code != 200:
                raise requests.HTTPError(resp.text)
            
            if resp.json()['Status']=='Success':
                return resp.json()['Response']
            
            if resp.json()['Status'] != 'Success' : 
                raise Exception(resp.json()['Reason'])
            
            else: return resp.json()
            
        except Exception as e :
            raise e




Ex = ExecutionEngine()

#Ex.datafrom_CHARTAPI(56631, datetime.datetime(2024,5,31),datetime.datetime(2024,5,31))
#df_fno = Ex.datafrom_CHARTAPI(26000, datetime.datetime(2024,6,7),datetime.datetime(2024,6,10), 'cash', 1) #banknifty
#df_fno = Ex.datafrom_CHARTAPI(26000, datetime.datetime(2024, 6, 10), datetime.datetime(2024,6,10), 'cash', 1)
#print(df_fno)
# 26000 is the token for NIFTY
# 26009 is the token for BANKNIFTY.


# For FNO: Only historical data is coming (2024-08-26 09:15:00 to 2024-08-27 15:29:00)
df_fno = Ex.datafrom_CHARTAPI(26009, datetime.datetime(2024,8,26), datetime.datetime(2024,8,28), "fno", 1) #banknifty
print(df_fno)

# For CASH: From startdate to Live data (2024-08-26 09:15:00 to 2024-08-28 11:44:00) Historical as well as Upto Live data
df_cash = Ex.datafrom_CHARTAPI(26009, datetime.datetime(2024, 8, 26), datetime.datetime(2024, 8, 28), "cash",1)  # banknifty
print(df_cash)
# while True:
#     df_cash = Ex.datafrom_CHARTAPI(26009, datetime.datetime(2024, 8, 26), datetime.datetime(2024, 8, 28), "cash", 1)  # banknifty
#
#     print("Open:",df_cash["Open"].iloc[-1])
#     print("High:", df_cash["High"].iloc[-1])
#     print("Low:", df_cash["Low"].iloc[-1])
#     print("Close:", df_cash["Close"].iloc[-1])
#     print("Volume:", df_cash["Volume"].iloc[-1])
#
#
#     time.sleep(60)

