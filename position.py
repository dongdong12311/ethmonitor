# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 22:56:44 2019

@author: dongdong
"""
import pytz
import okex.account_api as account
import okex.ett_api as ett
import okex.futures_api as future
import okex.lever_api as lever
import okex.spot_api as spot
import okex.swap_api as swap
from  dateutil.parser import parse
import datetime
import time
import sys
import requests
import os
import smtplib
from email.mime.text import MIMEText
msg_from='664560694@qq.com'                               
passwd='pjjxxlksiiqgbchd'                                  
msg_to='664560694@qq.com'
subject="新爆仓单"


      
class Param:
    def __init__(self):
        self.instrument_id =  'ETH-USD-190329'
        self.beishu = 10
      
class Loser():
    def __init__(self,timeindex,price,tradeside,size):
        self.timeindex = timeindex
        self.price = price
        self.tradeside = tradeside
        self.size = size 
class TimeCal:
    def __init__(self,timestamp):
        self.__timestamp = parse(timestamp)
        

    def relativetime(self):
        "相对于现在的时间"
        temp = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone('UTC')) - self.__timestamp        
        return temp.total_seconds()

class Order:
    "委托订单"
    def __init__(self,order_id,price,timestamp,ordertype):
        self.price = price
        self.timestamp = TimeCal(timestamp)
        self.orderid = order_id
        self.ordertype = ordertype
        
    
    def order_time_relative(self):
        "获取订单相对现在没有成交的时间 单位是秒"
        return self.timestamp.relativetime()
    
class Position:
    "持仓的数据"
    def __init__(self,tradeside,qty,avg_cost,ratio,liqui_price):
        "tradeside : 交易方向  qty: 合约张数 avg_cost :开仓价格 ratio 盈亏比例"
        self.tradeside = tradeside
        self.qty = int(qty)
        self.avg_cost =  float(avg_cost)
        self.ratio =float( ratio)
        self.liqui_price =float( liqui_price)
class API(Param):
    def __init__(self):
        super().__init__()
        api_key = '3cbbc362-4a31-4f02-8e19-8c8092a7bbd2'
        seceret_key = '4FC0928F9E7C73F536FF7334E305FDED'
        passphrase = 'dongdong'

        self.futureAPI = future.FutureAPI(api_key, seceret_key,passphrase, True)  
    def GetDepth(self,depth = 2):
        "获取市场深度数据"
        result={}
        result['order_info'] = []
        try:
            result = self.futureAPI.get_depth(self.instrument_id,depth)
        except:
            print("无法获取市场数据")
        return result   
    
    def GetLoser(self):
        "获取最新的爆仓订单"
        
        try:
            get = requests.get('https://www.okex.me/api/futures/v3/instruments/'+self.instrument_id+'/liquidation?status=1&from=1&limit=50')
        except:
            print("获取爆仓单失败")
            return []
        return  get.json()
    
    def best_ask(self):
        try:
            return self.GetDepth()['asks'][0][0]
        except:
            return None
    def best_bid(self):
        try:
    
            return self.GetDepth()['bids'][0][0]
        except:
            return None
    def get_position(self):
        
        try:
            results = self.futureAPI.get_specific_position(self.instrument_id) 
        except:
            print("获取持仓数据失败")
            return None 
        return results
  
    def close_position(self,position,price):
        "平仓 type	String	是	1:开多2:开空3:平多4:平空 "
        if position.tradeside == 1:
            otype = '3'
        else:
            otype = '4'
        try:
            self.futureAPI.take_order("ccbce5bb7f7344288f32585cd3adf357", self.instrument_id,otype,price,str(position.qty),'0',str(self.beishu))
        except:
            print("平仓失败")
            return False
        return True
    def cancel_order(self,order):
        "撤单"
        try:
            self.futureAPI.revoke_order(self.instrument_id,order.orderid)
        except:
            print("撤单失败")
            return False
        return True
    def  get_my_order_list(self):
        results = {}
        results['order_info'] = []
        try:
            results = self.futureAPI.get_order_list(0,1,2,50,self.instrument_id)
        except:
            print("获取未成交订单失败")
        return results
    def open_position(self,price,size,tradeside):
        "开仓"
        "match_price	String	否	是否以对手价下单(0:不是 1:是)，默认为0，当取值为1时。price字段无效"
        match_price  = str(0)
        "leverage	Number	是	要设定的杠杆倍数，10或20"
        leverage = str(10)
        if tradeside == 1:
            otype = str(1)

        if tradeside == -1:
            otype = str(2)
        try:
            self.futureAPI.take_order("ccbce5bb7f7344288f32585cd3adf357", self.instrument_id,otype, price, size, match_price, leverage)     
        except Exception as e:
            print("开仓失败")      
class Market(Param):
    def __init__(self,API):
        super().__init__()
        self.api = API
        self.filename = self.instrument_id+'_Loser.txt'
        if self.FileInit()==None:
            sys.exit()
    def FileInit(self):
        try:
            filesize = os.path.getsize(self.filename)
            if filesize == 0:
                d = {'loss': 0, 'size': 95, 
                     'price': 140.428, 'created_at': 
                         '2019-01-01T01:21:56.000Z', 'type': 3,
                         'instrument_id': self.instrument_id}
                files = str(d)
                file = open(self.filename,'w+')
                file.writelines(files+"\n")
                file.close()
                
        except FileNotFoundError:
            print(self.filename + ' not found!')
            return None
        return True
    def LastLose(self):
        filesize = os.path.getsize(self.filename)
        with open(self.filename, 'rb') as fp: # to use seek from end, must use mode 'rb'
            offset = -8                 # initialize offset
            while -offset < filesize:   # offset cannot exceed file size
                fp.seek(offset, 2)      # read # offset chars from eof(represent by number '2')
                lines = fp.readlines()  # read from fp to eof
                if len(lines) >= 2:     # if contains at least 2 lines
                    return lines[-1]    # then last line is totally included
                else:
                    offset *= 2         # enlarge offset
            fp.seek(0)
            lines = fp.readlines()
        s = lines[-1]
        return eval(s.decode())        
    def HasNewOrder(self):
        """判断是否是最新的爆仓单并且发送消息"""
        losers = []
        "载入日志中最新的爆仓订单"
        file = open(self.filename,'r')
        lastloser = eval(file.readlines()[-1])
        file.close()

        lastloser_time = parse(lastloser['created_at'])     
        "获取最新的爆仓订单"
        potential_losers = self.api.GetLoser()
        "自上而下遍历"
        file = open(self.filename,'a+')
        s=''
        for i in range(len(potential_losers)-1,-1,-1):            
            losetime =  parse(potential_losers[i]['created_at'])
            timedelta = losetime - lastloser_time            
            "如果爆仓订单的时间比现在的新"
            if timedelta.total_seconds() > 0:
            
                price = potential_losers[i]['price']
                loser = Loser(losetime,price,potential_losers[i]['type'],potential_losers[i]['size'])
                losers.append(loser)
                "发送消息"
                tradeside = self.GetOrderTypeName(potential_losers[i])
                timenow = (losetime+ datetime.timedelta(hours=8))
                timetext = timenow.strftime('%Y-%m-%d %H:%M:%S')    
                s+="__________________\n新增爆仓订单:\n爆仓价格：%.2f\n爆仓方向：%s\n爆仓时间:%s\n________"%(price,tradeside,timetext)
                "写入日志"
                files = str(potential_losers[i])+"\n"
                file.writelines(files)

        file.close()                
        return losers
    def GetOrderTypeName(self,potential_loser):
        "获取最新爆仓单的交易方向"
        if potential_loser['type'] == 3:
            temp = "多头"
        else:
            temp = "空头"
        return temp
  
    
    

        
  
    
        
    
class Account(Param):
    def __init__(self,API):
        super().__init__()
        self.api = API   
    def get_market_orders(self):
        "获取没有成交的订单"
        results = self.api.get_my_order_list()
        orders = []
        for result in results['order_info']:
            "order_id,price,timestamp,ordertype):"
            order = Order(result['order_id'],result['price'],result['timestamp'],result['type'])
            orders.append(order)
        return orders
    def GetPositions(self):
        results = self.api.get_position()
        if results is None:
            return 
        if len(results['holding']) > 1:
            print(results)
            sys.exit()
        if len(results['holding']) == 0:
            return None
        res = results['holding'][0]
        if res['long_qty'] != '0':
            "持有多头"
            "tradeside,qty,avg_cost,ratio,liqui_price"
            "res['long_avg_cost'] 由于okex采用的是标记价格  我们的浮动盈亏不应该采用标记价格"
            "获取最高买价"
            price = self.api.best_bid()
            if price is  None:
                return
            rate = (price-float(res['long_avg_cost']))/float(res['long_avg_cost'])*100*self.beishu
            position = Position(1,res['long_avail_qty'],res['long_avg_cost'],rate,res['long_liqui_price'])
        if res['short_qty'] != '0':
            "持有空头"
            "tradeside,qty,avg_cost,ratio,liqui_price"
            "最低卖价"
            price = self.api.best_ask()
            if price is  None:
                return
            rate = -(price-float(res['short_avg_cost']))/float(res['short_avg_cost'])*100*self.beishu
            position = Position(-1,res['short_avail_qty'],res['short_avg_cost'],rate,res['short_liqui_price'])
                
            
        return  position
    


    
    
class AccountMonitor:
    "账户监控模块"
    def __init__(self,myaccount,market,api):
        self.__account = myaccount
        self.market = market
        self.api = api
    def __monitor_market_orders(self):
        "监控市场上没有成交的订单"
        orders  = self.__account.get_market_orders()
        for order in orders:
            print(order.order_time_relative())
            if order.order_time_relative() > 2:
                "订单时间超过两分钟"
                "撤单"
                self.api.cancel_order(order)        
    def __monitor_position(self):
        position = self.__account.GetPositions()
        if position is  None:
            return 
        print(position.ratio)
        if abs(position.ratio) > 10 and position.qty > 0 :
            "如果收益超过+-10%"
            if position.tradeside == 1:                
                price = self.api.best_ask()-0.001
            else:
                price = self.api.best_bid()+0.001
            s = '平仓价格'+str(price)+' '
            print(s)
            self.api.close_position(position,str(price))

                
    def __monitor_loser(self):
        size = '10'
        losers = self.market.HasNewOrder()
        for loser in losers:  
            print("有新爆仓单 开仓")
            if float(loser.size) < 10:
                print("爆仓规模太小 没有开仓")
                print(loser.size)
                continue
            if loser.tradeside == 3:
                self.api.open_position(str(loser.price+1),size,1)
            if loser.tradeside == 4:
                self.api.open_position(str(loser.price-1),size,-1)
    def monitor(self):
        
        self.__monitor_loser()
        self.__monitor_market_orders()
        self.__monitor_position()
        
API = API()
myaccount = Account(API)
market  = Market(API)
a = AccountMonitor(myaccount,market,API)
while 1:
    time.sleep(0.21)
    b = a.monitor()

    
    
    