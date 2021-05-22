import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../")
from modules import binance_anacrypt
from modules import mytelebot

#interval_list=["15m","30m","1h","2h","6h","12h","1d","3d","1w","1M"]
interval_list=["1h","2h","6h","1d","3d","1w","1M"]
coinlist=["BTCUSDT","ETHEUR","MATICUSDT","ADAUSDT","XLMUSDT","SOLUSDT","XRPEUR","DOGEUSDT","YFIEUR","LTCUSDT"]
attr_list=["EMA7 sl","EMA15 sl","Recmnd>>"]


def send_crypto_updates():
	binance_anacrypt.gen_pandas_crypt_table(coinlist,interval_list,attr_list,rsi_thr=[35.,65.],ext=".png",movie_fmt="gif")
	mybot=mytelebot.init_mybot(test=False) # Use test=True for testing, else you spam everyone.
	mybot.update_subscriber_preferences()
	mybot.broadcast_cryptoupdate()

if __name__ == "__main__":
	send_crypto_updates()
