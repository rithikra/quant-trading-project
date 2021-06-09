from QuantConnect.Data.Custom.Tiingo import *
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import json
# Most Code taken from: https://www.quantconnect.com/forum/discussion/5983/feed-live-data-from-bitfinex-to-a-live-strategy/p1
class CompetitionExampleAlgorithm(QCAlgorithm):

    def Initialize(self):
        
        self.SetStartDate(2016, 1, 1) 
        self.SetCash(100000)
        
        # self.SetBrokerageModel(BrokerageName.Bitfinex, AccountType.Cash)
        consolidator = QuoteBarConsolidator(timedelta(minutes = 5))
        consolidator.DataConsolidated += self.OnDataConsolidated
        
        tickers = ["BTCUSD"]
        symbols = []
        for ticker in tickers:
            self.Debug(ticker)
            self.AddCrypto(ticker, Resolution.Minute, Market.Bitfinex)
            # Register the consolidator for data.
            self.SubscriptionManager.AddConsolidator(ticker, consolidator)
            symbols.append(Symbol.Create(ticker, SecurityType.Crypto, Market.Bitfinex))
        
        
        self.Debug("Added Crypto to Securities Map")
        
        
        
        # attach our event handler. The event handler is a function that will
        # be called each time we produce a new consolidated piece of data.
        
        
        
        
        self.rsi = RelativeStrengthIndex(10, MovingAverageType.Simple) # define Indicator
        
        ## Set Universe Selection Model
        self.SetUniverseSelection(ManualUniverseSelectionModel(symbols))
        
        
        ## Set Alpha Model
        self.SetAlpha(NewsSentimentAlphaModel())

        ## Set Portfolio Construction Model
        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())

        ## Set Execution Model
        self.SetExecution(ImmediateExecutionModel())

        ## Set Risk Management Model
        self.SetRiskManagement(NullRiskManagementModel())
        self.Debug("Initilize is complete")
        
   
    def OnData(self, data):
        self.Debug("In on data")
        # self.Debug("Data bars" + data.Bars["BTCUSD"].Close)
        
    # fires when a new piece of data is produced.
    def OnDataConsolidated(self, sender, bar):
        self.Debug("In DataConsolidated")
        self.Debug(str(self.Time) + " " + str(bar))
        
        agg_data = self.get_5mins_Bitfinex()
        self.rsi.Update(self.Time, agg_data[3])
        if self.rsi.IsReady:
            rsi_value = self.rsi.Current.Value
            self.Debug('rsi_value {}'.format(rsi_value))
            
            
    def get_5mins_Bitfinex(self):
        end_time = datetime.now() # past 5 minutes time
        start_5mins = end_time - timedelta(minutes=5) # convert current time to timestamp
        end_tstamp = round(datetime.timestamp(end_time)*1000,0) # convert past 5 minutes to timestamp
        start_5mins_tstamp = round(datetime.timestamp(start_5mins)*1000,0)
        
        getdata_time = datetime.now()
        url = 'https://api-pub.bitfinex.com/v2/trades/tBTCUSD/hist?limit=5000&start={}&end={}&sort=-1'.format(start_5mins_tstamp, end_tstamp)
        string = self.Download(url)
        self.Debug('data downloading time: {}'.format(datetime.now()-getdata_time))
        
            ## Insert method for parsing string into the dataframe you defined as data_df
        ## Note that Download() returns a string and not a json
        ## 'requests' does not work here
        
        data = json.loads(string)
        data_df = pd.DataFrame(data, columns = ['id','date','volume','price'])
            
        self.Debug('data size {} rows'.format(data_df.shape[0]))
            
    
        
        # aggregate the data
        volume = data_df.volume.abs().sum()
        volume_pos = data_df.volume.apply(lambda x: x if x >0 else 0).sum() # only take trade volume resulted from a taker buy order
        open_price = data_df.price.values[0]
        close_price = data_df.price.values[-1]
        high_price = data_df.price.max()
        low_price = data_df.price.min()
        agg_data = [open_price, high_price, low_price, close_price, volume, volume_pos]
        
        ## Insert trading logic and placing orders
        
        
        return agg_data


class NewsSentimentAlphaModel:
    
    def __init__(self):
        
        # the sample pool of word sentiments
        self.wordSentiment = {
            "bad": -0.5, "good": 0.5, "negative": -0.5, 
            "great": 0.5, "growth": 0.5, "fail": -0.5, 
            "failed": -0.5, "success": 0.5, "nailed": 0.5,
            "beat": 0.5, "missed": -0.5, "profitable": 0.5,
            "beneficial": 0.5, "right": 0.5, "positive": 0.5, 
            "large":0.5, "attractive": 0.5, "sound": 0.5, 
            "excellent": 0.5, "wrong": -0.5, "unproductive": -0.5, 
            "lose": -0.5, "missing": -0.5, "mishandled": -0.5, 
            "un_lucrative": -0.5, "up": 0.5, "down": -0.5,
            "unproductive": -0.5, "poor": -0.5, "wrong": -0.5,
            "worthwhile": 0.5, "lucrative": 0.5, "solid": 0.5
        }
        self.day = -1
        self.custom = []
        self.symbolData = {};
        
    
    def Update(self, algorithm, data):
        print("In update")
        insights = []
        
        # Run the model daily
        if algorithm.Time.day == self.day:
            return insights
            
        self.day = algorithm.Time.day
        
        
        weights = {}
        
        # Fetch the wordSentiment data for the active securities and trade on any
        for security in self.custom:
            
            if not data.ContainsKey(security):
                continue
                
            news = data[security]
            
            descriptionWords = news.Description.lower().split(" ")
            # Get the intersection words between sentiment sample pool and news description
            intersection = set(self.wordSentiment.keys()).intersection(descriptionWords)
            # Calculate the score sum of word sentiment
            sentimentSum = sum([self.wordSentiment[i] for i in intersection])

            if sentimentSum > 0:
                weights[security.Underlying] = sentimentSum
        
        # Sort securities by sentiment ranking, 
        count = min(10, len(weights)) 
        if count == 0:
            return insights
            
        # Order the sentiment by value and select the top 10
        sortedbyValue = sorted(weights.items(), key = lambda x:x[1], reverse=True)
        selected = {kv[0]:kv[1] for kv in sortedbyValue[:count]}
        
        # Populate the list of insights with the selected data where the sentiment sign is the direction and its value is the weight
        closeTimeLocal = Expiry.EndOfDay(algorithm.Time)
        for symbol, weight in selected.items(): 
            insights.append(Insight.Price(symbol, closeTimeLocal, InsightDirection.Up, None, None, None, abs(weight)))
        print("Our insights: " + insights)
        return insights
        
        
    def OnSecuritiesChanged(self, algorithm, changes): # executes whenever we add/remove securities 
        for security in changes.AddedSecurities:
            # Tiingo's News is for US Equities
            if security.Type == SecurityType.Equity:
                self.custom.append(algorithm.AddData(TiingoNews, security.Symbol).Symbol)
                
                
# This structures each asset to have their own 
class SymbolData():
    def __init__(self, security, algorithm):
        self.Security = security
        self.Symbol = security.Symbol
        
        # consolidate data                          
        self.thirtyMinuteConsolidator = TradeBarConsolidator(timedelta(minutes=30))
        #self.thirtyMinuteConsolidator.DataConsolidated += self.OnThirtyMinuteBarHandler
        algorithm.SubscriptionManager.AddConsolidator(security.Symbol, self.thirtyMinuteConsolidator)
        algorithm.RegisterIndicator(security.Symbol, self.ichimoku, self.thirtyMinuteConsolidator)