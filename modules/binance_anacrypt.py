import os
import glob
import time
import json
import pytz
import requests
import numpy as np
import collections
import pandas as pd
import dataframe_image as dfi
import datetime
import imageio
path_to_this_file=os.path.dirname(os.path.abspath(__file__))

# Available statistical attributes: [MACD,RSI,Recmnd>>,EMA7 sl,EMA30 sl]
attr_list=["MACD","RSI","Recmnd>>","EMA7 sl","EMA15 sl","EMA30 sl"]

def gen_pandas_crypt_table(coinpair_list,interval_list,attr_list=attr_list,rsi_thr=[35.,65.],ext=".jpeg",movie_fmt="gif"):
	cryptstat=get_crypto_dict(coinpair_list,interval_list)
	stat=collections.OrderedDict()
	stat["coinpair"]=[]
	stat["cval"]=[]
	stat["stat"]=[]
	for lst in interval_list:
		stat[lst]=[]

	# This prints out all the indicators like MACD and RSI
	for coinpair in np.sort(coinpair_list):
		for attr in attr_list:
			stat["coinpair"]=stat["coinpair"] + [coinpair]
			stat["cval"]=stat["cval"] + [str(cryptstat[coinpair]["cval"])]
			stat["stat"]=stat["stat"]+[attr]
			for intr in interval_list:
				stat[intr]=stat[intr] + [cryptstat[coinpair][intr][attr]]

	pd.set_option('precision', 3)
	buysell=pd.DataFrame(stat)
	buysell.set_index(["coinpair","cval","stat"],inplace=True)
	buysell=buysell.applymap(lambda x: "+"+str(round(x,3)) if isinstance(x,float) and x>0 else x)
	buysell=buysell.style.applymap(_color_red_or_green)


	timestamp_local=str(datetime.datetime.now())
	timestamp_local=timestamp_local.replace(":","-")
	date_stamp=timestamp_local[:10]

	timestamp_ind = str(datetime.datetime.now(pytz.timezone('Asia/Calcutta')))
	timestamp_ind=timestamp_ind.replace(":","-")

	caption="Binance : " + timestamp_local[:-10]  + " " + time.tzname[0] + " / " + timestamp_ind[:-16][11:] + " IST"
	buysell=buysell.set_caption(caption)

	outpath=path_to_this_file + "/../outdata/" + date_stamp + "/"
	ensure_dir(outpath)
	filename=outpath + "/buysell_idicator_" + timestamp_local[:-10].replace(" ","_") + ext
	#dfi.export(buysell,filename,table_conversion='matplotlib')
	dfi.export(buysell,filename,chrome_path=None)
	#dfi.export(buysell,filename,chrome_path='/Applications/Google Chrome Canary.app/Contents/MacOS/')

	if movie_fmt=="mp4":
		gen_mp4(figpath=outpath)
	else:
		gen_gif(figpath=outpath)

def _color_red_or_green(val):
	if isinstance(val, str):
		if "SELL" in val.upper():
				color = 'red'
		elif "BUY" in val.upper():
				color = 'green'
		elif val.upper()=="NA":
				color = 'gray'
		elif "+" in val:
			color="cyan"
		elif "-" in val:
			color="pink"
		else:
			color="yellow"
	else:
		if val<0:
			color = "pink"
		else:
			color = "cyan"
	return 'background-color: %s' % color

def gen_gif(figpath):
	'''
	Compares the latest statistics with one compared in the prior evaluation
	'''
	list_of_files = glob.glob(figpath + "/*")
	list_of_files = [f for f in list_of_files if "gif" not in f]
	new_file = max(list_of_files, key=os.path.getctime)

	gifpath=figpath + "/gif/" ; ensure_dir(gifpath)
	outfile=gifpath + "compare_crypto_stat.gif"
	
	if len(list_of_files) >=2:
		list_of_files.remove(new_file)
		old_file=max(list_of_files, key=os.path.getctime)

		images = []
		for filename in [new_file,old_file]:
			images.append(imageio.imread(filename))
			imageio.mimsave(outfile, images, fps=1.1)
	#		os.system("rm " + old_file)
	else:
		images = []
		for filename in [new_file,new_file]:
			images.append(imageio.imread(filename))
			imageio.mimsave(outfile, images, fps=1.1)

def gen_mp4(figpath):
	'''
	Compares the latest statistics with one compared in the prior evaluation
	'''
	list_of_files = glob.glob(figpath + "/*")
	list_of_files = [f for f in list_of_files if "gif" not in f]
	new_file = max(list_of_files, key=os.path.getctime)
	
	gifpath=figpath + "/gif/" ; ensure_dir(gifpath)
	outfile=gifpath + "compare_crypto_stat.mp4"
	
	w = imageio.get_writer(outfile, format='FFMPEG', mode='I', fps=1.3,
						codec='h264_vaapi',
						output_params=['-vaapi_device',
                                      '/dev/dri/renderD128',
                                      '-vf',
                                      'format=gray|nv12,hwupload'],
                       pixelformat='vaapi_vld')

	if len(list_of_files) >=2:
		list_of_files.remove(new_file)
		old_file=max(list_of_files, key=os.path.getctime)
	
		for filename in [new_file,old_file]:
			w.append_data(imageio.imread(filename))
		w.close()
		os.system("rm " + old_file)
	else:
		for filename in [new_file,new_file]:
			w.append_data(imageio.imread(filename))
		w.close()

def get_crypto_dict(coinpair_list,interval_list,rsi_thr=[30.,70.]):
	cryptstat={}
	for coinpair in np.sort(coinpair_list):
		cryptstat[coinpair]={}
		for intr in interval_list:
			cryptstat[coinpair][intr]={}
			
			try:
				crypto_ts=get_eval_crypto_stat(coinpair,intr)
				crypto_ts.get_stat_recommendation(rsi_thr=rsi_thr)
				cryptstat[coinpair][intr]={"RSI":crypto_ts.rsi_buysell,
									"MACD":crypto_ts.macd_buysell,
									"Recmnd>>":crypto_ts.buysell,
									"EMA7 sl":crypto_ts.ema7_sl,
									"EMA15 sl":crypto_ts.ema15_sl,
									"EMA30 sl":crypto_ts.ema30_sl}
				cryptstat[coinpair]["cval"]=crypto_ts.cval
			except:
	#				 print("Failed for " + coinpair + " at " + intr)
				cryptstat[coinpair][intr]={"RSI":"NA",
										"MACD":"NA",
										"Recmnd>>":"NA",
										"EMA7 sl":"NA",
										"EMA15 sl":"NA",
										"EMA30 sl":"NA"}
				cryptstat[coinpair]["cval"]="NA"
	return cryptstat

class get_eval_crypto_stat(object):
	def __init__(self,curpair,interval="15m"):
		
		# Data comes in with UTC time stamp. This offset is used to shift to local time.
		now_timestamp = time.time()
		self.offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
		self.curpair=curpair
		self.interval=interval
		self.url=url_build(symbol=self.curpair,interval=self.interval)
		response = requests.get(self.url)
		self.response_dict = json.loads(response.text)
		self.dataframe=pd.DataFrame.from_dict(self.response_dict)
		
		candle_columns = ["Open time","Open","High","Low","Close","Volume","Close time","Quote asset volume",
							   "Number of Trades","Taker buy base asset volume","Taker buy quote asset volume",
							   "Ignore."]
		self.dataframe.columns=candle_columns
		self.dataframe['Open time'] = pd.to_datetime(self.dataframe['Open time'].astype('int'),unit='ms')
		self.dataframe['Open time'] = self.dataframe['Open time'] + self.offset
		self.dataframe['Close time'] = pd.to_datetime(self.dataframe['Close time'].astype('int'),unit='ms')
		self.dataframe['Close time'] = self.dataframe['Close time'] + self.offset
		self.dataframe[self.dataframe.columns[1:5]] = self.dataframe[self.dataframe.columns[1:5]].astype("float")
		
		self.dataframe["EMA7"]=pd.Series.ewm(self.dataframe["Close"], span=7).mean()
		self.dataframe["EMA15"]=pd.Series.ewm(self.dataframe["Close"], span=15).mean()
		self.dataframe["EMA30"]=pd.Series.ewm(self.dataframe["Close"], span=30).mean()
		self.dataframe["EMA90"]=pd.Series.ewm(self.dataframe["Close"], span=90).mean()
		self.dataframe["EMA200"]=pd.Series.ewm(self.dataframe["Close"], span=200).mean()
		
		self.dataframe["MACD"]=pd.Series.ewm(self.dataframe["Close"], span=12).mean()-pd.Series.ewm(self.dataframe["Close"], span=26).mean()
		self.dataframe["SL"]=pd.Series.ewm(self.dataframe["MACD"], span=9).mean() # Signal line
		
		self.dataframe["RSI"]=calc_rsi(self.dataframe)
		self.dataframe=calc_bollinger(self.dataframe,period=21)

	def make_candle_stick_plot(self,):
		import plotly.graph_objects as go
		import plotly.express as px
		
		fig = go.Figure(data=[
			go.Candlestick(x=self.dataframe['Open time'],open=self.dataframe['Open'],
											 high=self.dataframe['High'],low=self.dataframe['Low'],
											 close=self.dataframe['Close'],name=""),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["EMA7"],line=dict(color='black', width=2),name='EMA7'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["EMA30"],line=dict(color='blue', width=2),name='EMA30'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["EMA90"],line=dict(color='magenta', width=2),name='EMA90'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["EMA200"],line=dict(color='red', width=2),name='EMA200'),
			#go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["MA-TP"],line=dict(color='black', width=2),name='MA-TP 21'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["BOLLU"],line=dict(color='black', width=2),name='BOLL-U 21'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["BOLLD"],line=dict(color='black', width=2),name='BOLL-D 21')
			])
		fig.update_layout(xaxis_rangeslider_visible=False,title_text=self.curpair,title_x=0.5,title_y=0.9)
		fig.show()

	def make_macd_plot(self,):
		import plotly.graph_objects as go
		import plotly.express as px
		fig = go.Figure(data=[
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["MACD"],line=dict(color='magenta', width=2),name='MACD'),
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["SL"],line=dict(color='black', width=2),name='Signal'),
	#             go.Scatter(x=self.dataframe['Open time'], y=(self.dataframe["MACD"]-self.dataframe["SL"])/abs(self.dataframe["SL"]),line=dict(color='black', width=2),name='Signal')
			])
		fig.add_hline(y=0,line=dict(color='black', width=2,dash='dash'))
		fig.update_layout(xaxis_rangeslider_visible=False,title_text="MACD",title_x=0.5,title_y=0.9)
		
		fig.show()

	def make_rsi_plot(self,):
		import plotly.graph_objects as go
		import plotly.express as px
		fig = go.Figure(data=[
			go.Scatter(x=self.dataframe['Open time'], y=self.dataframe["RSI"],line=dict(color='red', width=2))
			])
		fig.add_hline(y=70,line=dict(color='black', width=2))
		fig.add_hline(y=30,line=dict(color='black', width=2))
		fig.update_layout(xaxis_rangeslider_visible=False,title_text="RSI",title_x=0.5,title_y=0.9)
		fig.show()

	def get_stat_recommendation(self,rsi_thr=[30.,70.]):
		self.macd_zone,self.macd_buysell=macd_indicator(self.dataframe)
		self.rsi_zone,self.rsi_buysell,self.rsi_buy_str,self.rsi_sell_str=rsi_indicator(self.dataframe,rsi_thr)
		
		self.zone="HOLD"
		if self.macd_zone=="Buy" and self.rsi_zone=="Buy":
			self.zone="BUY"
		if self.macd_zone=="Sell" and self.rsi_zone=="Sell":
			self.zone="SELL"
		
		self.buysell="HOLD"
		if self.macd_buysell=="Buy" and self.rsi_buysell=="Buy":
			self.buysell="BUY" + "[" + str(round(self.rsi_buy_str,1)) + "]"
		if self.macd_buysell=="Sell" and self.rsi_buysell=="Sell":
			self.buysell="SELL" + "[" + str(round(self.rsi_sell_str,1)) + "]"
		
		self.ema7_sl=np.diff(np.array(self.dataframe["EMA7"]))[-2]*100/np.abs(self.dataframe["EMA30"].iloc[-2])
		self.ema15_sl=np.diff(np.array(self.dataframe["EMA15"]))[-2]*100/np.abs(self.dataframe["EMA30"].iloc[-2])

		# This is dummy, normalized by EMA60. Need to clean up or revise.
		self.ema30_sl=np.diff(np.array(self.dataframe["EMA30"]))[-2]*100/np.abs(self.dataframe["EMA90"].iloc[-2])

		self.cval=self.dataframe["Close"].iloc[-1]

def rsi_indicator(dataframe,rsi_thr=[30.,70.]):
	rsi=np.array(dataframe["RSI"])
	smooth_rsi=np.array(pd.Series.ewm(dataframe["RSI"], span=9).mean())
	df = np.diff(smooth_rsi)
	#	df = np.diff(rsi)

	buysell="Hold"
	zone="Hold"
	# This number is supposed to indicate how strong the buy sell signal is
	buy_strength=0.
	sell_strength=0.
	if rsi[-2]>rsi_thr[1]:
		zone="Sell"
		# Setting max to 85 amplifies the sell signal.
		sell_strength=(rsi[-2]-rsi_thr[1])/(85.-rsi_thr[1])
		if df[-2]<0:
			buysell="Sell"
	elif rsi[-2]<rsi_thr[0]:
		zone="Buy"
		# Setting max to 15 amplifies the buy signal.
		buy_strength=(rsi_thr[0]-rsi[-2])/(rsi_thr[0]-15.)
		if df[-2]>0:
			buysell="Buy"

	return buysell,zone,buy_strength,sell_strength

def macd_indicator(dataframe):
	macd=np.array(dataframe["MACD"])
	#signal=np.arange(dataframe["SL"])
	# You could check if MACD is above or below signal line, but then we may loose opportunities.
	smooth_y=np.array(pd.Series.ewm(dataframe["MACD"], span=5).mean())
	df = np.diff(smooth_y)
	#df = np.diff(macd)

	buysell="Hold"
	zone="Hold"

	if macd[-2]>0.:
		zone="Sell"
		if df[-2]<=0.:
			buysell="Sell"
	elif macd[-2]<0:
		zone="Buy"
		if df[-2]>=0:
			buysell="Buy"

	return buysell,zone

def calc_rsi(df, periods = 14, ema = True):
    """
    Returns a pd.Series with the relative strength index.
    """
    close_delta = df['Close'].diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
	
    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window = periods, adjust=False).mean()
        ma_down = down.rolling(window = periods, adjust=False).mean()
	
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi

def calc_bollinger(df,period=21):
	df["TP"]=(df["High"] + df["Low"] + df["Close"])/3.
	df["STD"]=df["TP"].rolling(period).std(ddof=0)
	df["MA-TP"]=df["TP"].rolling(period).mean()
	df["BOLLU"]=df["MA-TP"] + 2.*df["STD"]
	df["BOLLD"]=df["MA-TP"] - 2.*df["STD"]
	return df

def url_build(symbol="XRPUSDT", interval="1m"):
    url_base = "https://api.binance.com"
    url_endpoint = "/api/v1/klines"
    url_final = url_base + url_endpoint + "?symbol={}&interval={}".format(symbol,interval)
    return url_final

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
