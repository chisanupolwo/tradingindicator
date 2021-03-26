import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import starfishX as sx


class Indicator():

    def __init__(self, symbol):
        self.symbol = symbol

    def ema(self):
        #Retrieve stock data
        df = sx.loadHistData([self.symbol], start='2018-01-01', end='2019-01-01', Volume =False)

        #EMA
        dataf = df[self.symbol].to_frame()
        EMA15= df[self.symbol].ewm(span = 15, adjust=True).mean()
        EMA45 = df[self.symbol].ewm(span = 45, adjust=True).mean() #spanday = 14
        EMA100 = df[self.symbol].ewm(span = 100, adjust=True).mean() 
        dataf['EMA15'] = EMA15
        dataf['EMA45'] = EMA45
        dataf['EMA100'] = EMA100

        #Buy sell
        cash=100000
        SigBuy, SigSell = [], []
        #Decision Rules of Buy
        dataf['Signal_Mid'] = np.where(dataf['EMA15']>dataf['EMA45'],1.0,0)
        dataf['Signal_Long'] = np.where(dataf['EMA15']>dataf['EMA100'],1.0,0)
        #Position
        dataf['Position_Mid'] = dataf['Signal_Mid'].diff()
        dataf['Position_Long'] = dataf['Signal_Long'].diff()

        #Set init var
        init_cash=100000
        dataf['Buy_Sell'] = np.zeros(len(dataf.index))
        dataf['Cur_cash'] = np.zeros(len(dataf.index))
        dataf['Num_stock'] = np.zeros(len(dataf.index))
        dataf['Port_val'] = np.zeros(len(dataf.index))
        dataf['Total_val'] = np.zeros(len(dataf.index))
        dataf['Cur_cash'].iloc[0] = init_cash
        
        #Setup Vars
        buy_price = []
        sell_price = []
        
        type_buy = []
        type_sell = []

        dataf['Cur_cash'].iloc[0] = init_cash
        
        #Decision
        for num in range(1,len(dataf.index)):
            #Buy Condition Short/Mid
            if dataf.Position_Mid.iloc[num] == 1 and dataf.Position_Long.iloc[num] == 0:
                dataf.iloc[num, dataf.columns.get_loc('Buy_Sell')] = 'Buy60' #Status for indexing
                buy_price.append(dataf[f'{dataf.columns[0]}'].iloc[num]) #Append Price
                type_buy.append('Buy60') #Status
                dataf.iloc[num, dataf.columns.get_loc('Num_stock')] = np.floor(0.6*dataf['Cur_cash'].iloc[num-1]/dataf[f'{dataf.columns[0]}'].iloc[num])
                dataf.iloc[num, dataf.columns.get_loc('Port_val')] = dataf[f'{dataf.columns[0]}'].iloc[num]*dataf['Num_stock'].iloc[num]
                #Update Current Cash
                dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1] - dataf.Port_val.iloc[num]
                #Total Value ==> Cur_cash+Port_Value
                dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]
                
            #Buy Consition Short/Long
            elif dataf.Position_Long.iloc[num] == 1:
                dataf.iloc[num, dataf.columns.get_loc('Buy_Sell')] = 'BuyAll'
                buy_price.append(dataf[f'{dataf.columns[0]}'].iloc[num])
                type_buy.append('BuyAll')
                dataf.iloc[num, dataf.columns.get_loc('Num_stock')] =np.floor(dataf['Cur_cash'].iloc[num-1]/dataf[f'{dataf.columns[0]}'].iloc[num])
                dataf.iloc[num, dataf.columns.get_loc('Port_val')] = dataf[f'{dataf.columns[0]}'].iloc[num]*dataf['Num_stock'].iloc[num]
                #Update Current Cash
                dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1] - dataf.Port_val.iloc[num]
                #Total Value ==> Cur_cash+Port_Value
                dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]
                
            #Sell Condition Short/Mid
            elif dataf.Position_Mid.iloc[num] == -1 and dataf.Position_Long.iloc[num] == 0:
                dataf.iloc[num, dataf.columns.get_loc('Buy_Sell')] = 'Sell60'
                sell_price.append(dataf[f'{dataf.columns[0]}'].iloc[num])
                
                #Conditional Sell ==> Check up what the last order is?
                if type_buy[len(type_buy)-1] == 'Buy60': #Buy60 ==> SellAll
                    dataf.iloc[num, dataf.columns.get_loc('Num_stock')] = 0
                    sell_val = dataf[f'{dataf.columns[0]}'].iloc[num]* dataf['Num_stock'].iloc[num-1]
                    dataf.iloc[num, dataf.columns.get_loc('Port_val')] = 0
                    #Update Current Cash
                    dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1] + sell_val
                    #Total Value ==> Cur_cash+Port_Value
                    dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]
                
                if type_buy[len(type_buy)-1] == 'BuyAll': #Remain 40% of Port
                    dataf.iloc[num, dataf.columns.get_loc('Num_stock')] = dataf.Num_stock.iloc[num-1]*0.4
                    sell_val = dataf[f'{dataf.columns[0]}'].iloc[num]* dataf['Num_stock'].iloc[num-1]*0.6
                    dataf.iloc[num, dataf.columns.get_loc('Port_val')] = dataf.Num_stock.iloc[num]*dataf[f'{dataf.columns[0]}'].iloc[num]
                    #Update Current Cash
                    dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1]+ sell_val
                    #Total Value ==> Cur_cash+Port_Value
                    dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]
                    
                    
            #Sell Condition Short/Long #Sell_all eventually
            elif dataf.Position_Long.iloc[num] == -1:
                dataf.iloc[num, dataf.columns.get_loc('Buy_Sell')] = 'SellAll'
                sell_price.append(dataf[f'{dataf.columns[0]}'].iloc[num])
                
                if type_buy[len(type_buy)-1] == 'Buy60' or type_buy[len(type_buy)-1] == 'BuyAll':
                    dataf.iloc[num, dataf.columns.get_loc('Num_stock')] = 0
                    sell_val = dataf[f'{dataf.columns[0]}'].iloc[num]* dataf['Num_stock'].iloc[num-1]
                    dataf.iloc[num, dataf.columns.get_loc('Port_val')] = 0
                    #Update Current Cash
                    dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1] + sell_val
                    #Total Value ==> Cur_cash+Port_Value
                    dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]
                    
            #Holding Position
            else:
                dataf.iloc[num, dataf.columns.get_loc('Buy_Sell')] = 'Hold'
                dataf.iloc[num, dataf.columns.get_loc('Num_stock')] = dataf.Num_stock.iloc[num-1]
                dataf.iloc[num, dataf.columns.get_loc('Port_val')] = dataf[f'{dataf.columns[0]}'].iloc[num]*dataf['Num_stock'].iloc[num]
                #Remain cash
                dataf.iloc[num, dataf.columns.get_loc('Cur_cash')] = dataf.Cur_cash.iloc[num-1]
                #Total Value ==> Cur_cash+Port_Value
                dataf.iloc[num, dataf.columns.get_loc('Total_val')] = dataf.Port_val.iloc[num]+ dataf.Cur_cash.iloc[num]

        return {
            "buy_price": buy_price, 
            "buy_type": type_buy, 
            "sell_price": sell_price, 
            "sell_type": type_sell
        }