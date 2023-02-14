from kivy.uix.screenmanager import ScreenManager, Screen
from dateutil.relativedelta import relativedelta
from matplotlib.pyplot import figure
import matplotlib.pyplot as plt
from qbstyles import mpl_style
from kivy.lang import Builder
from datetime import date
from kivy.app import App
import yfinance as yf
import matplotlib
import datetime


class StockInfo:

    def __init__(self, ticker, start, end, open, close, high, low, volume):
        self.ticker = ticker
        self.start = start
        self.end = end
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume

    def png(self, title, rsi, mfi, imi, sma, ss):
        mpl_style(dark=True)
        font = {'family': 'serif', 'weight': 'bold', 'size': 12}
        matplotlib.rc('font', **font)
        wedge_props = {'width': .3, 'edgecolor': 'white', 'linewidth': 2}
        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(13, 6.285)
        plt.clf()

        # Break the overall graph into different sections so we can have multiple graphs.
        ax = plt.subplot2grid((2, 4), (0, 0), colspan=4)
        # zorder, alpha and lw will add an afterglow for the graphs lines.
        ax.plot(self.high, color='lime', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.high, label="High", color='lime')
        ax.plot(self.low, color='#FF00FF', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.low, label="Low", color='#FF00FF')
        ax.plot(self.close, color='cyan', zorder=5, alpha=0.1, lw=8)
        ax.plot(self.close, label="Close", color='cyan')
        ax.legend(bbox_to_anchor=(1.1, 1.025))
        plt.title(title.capitalize() + ' Stock Info')
        ax.grid(color='white', linestyle='-', linewidth=0.1)

        # Underneath the HLC (high, low, close) graph we will make gauges for all the RSI, MFI and IMI values.
        ax1 = plt.subplot2grid((2, 4), (1, 0), colspan=1)
        ax1.pie([rsi, (100 - rsi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        ax2 = plt.subplot2grid((2, 4), (1, 1), colspan=1)
        ax2.pie([mfi, (100 - mfi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        ax3 = plt.subplot2grid((2, 4), (1, 2), colspan=1)
        ax3.pie([imi, (100 - imi)], wedgeprops=wedge_props, startangle=90, colors=['#FF00FF', '#808080'])
        plt.text(-6, 0, rsi, ha='center', va='center')
        plt.text(-8, 0, "     RSI:")
        plt.text(-3, 0, mfi, ha='center', va='center')
        plt.text(-5, 0, "     MFI:")
        plt.text(0, 0, imi, ha='center', va='center')
        plt.text(-2, 0, "     IMI:")

        # Add values as text next to gauges.
        text_string = '    Stock Info:\n\nSMA:      %.2f\nClose:     %.2f\nTrend:    %s\nTrade:     ' \
                      '%s\n\n' % (sma[-1], self.close[-1], market_trend(), ss)
        plt.text(2, -1, text_string)

        # Save the graphs as a png to be able to view or use in something like Flask.
        return plt.savefig("StockInfo.png")

    # Calculates the simple moving average of the stock.
    def sma(self, window_size):
        moving_averages = []
        for i in range((len(self.close) - 1) - window_size + 1):
            window = self.close[i: i + window_size]
            window_average = sum(window) / window_size
            moving_averages.append(round(window_average, 2))
        return moving_averages

    # Calculates the relative strength index of the stock.
    def rsi(self):
        closing_prices = self.close[::-1]
        gain = []
        loss = []
        for i in range(len(closing_prices) - 1):
            change = closing_prices[i] - closing_prices[i + 1]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        ave_gain = (sum(gain) / len(gain))
        ave_loss = abs(sum(loss) / len(loss))
        relative_strength = ave_gain / ave_loss
        return round(100 - (100 / (1 + relative_strength)), 2)

    # Calculates the money flow index of the stock.
    def mfi(self):
        daily_averages = []
        gain = []
        loss = []
        for i in range(len(self.close)):
            daily_average = (self.low[i] + self.high[i] + self.close[i]) / 3
            daily_averages.append(daily_average)
        for i in range(len(daily_averages) - 1):
            change = daily_averages[i + 1] - daily_averages[i]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        money_ratio = abs(sum(gain)) / abs(sum(loss))
        return round(100 - (100 / (1 + money_ratio)), 2)

    # Calculates the intraday momentum index of the stock.
    def imi(self):
        closing_prices = self.close[::-1]
        gain = []
        loss = []
        for i in range(len(closing_prices) - 1):
            change = closing_prices[i] - closing_prices[i + 1]
            if change >= 0:
                gain.append(change)
            else:
                loss.append(change)
        return round((sum(gain) / (sum(gain) + abs(sum(loss)))) * 100, 2)

    # Quick calculation to see if you should buy, sell, or hold.
    def stock_strength(self, rsi, mfi, imi, sma):
        trade = 0
        if rsi >= 70:
            trade += 1
        elif rsi <= 30:
            trade -= 1
        else:
            trade += 0
        if mfi >= 80:
            trade += 1.5
        elif mfi <= 20:
            trade -= 1.5
        else:
            trade += 0
        if imi >= 70:
            trade += 1.5
        elif imi <= 30:
            trade -= 1.5
        else:
            trade += 0
        difference = sma[-1] - self.close[-1]
        percent = difference / self.close[-1]
        if percent >= 0.02:
            trade += 1
        if percent <= -0.02:
            trade -= 1
        else:
            trade += 0
        if trade >= 2:
            return "Sell"
        if trade <= -2:
            return "Buy"
        else:
            return "Hold"


# Calculation to see if the market is bullish or bearish.
def market_trend():
    sp500 = yf.Ticker('^GSPC')
    data = sp500.history(period='1y')
    last_close = data['Close'][-1]
    average_close = data['Close'].mean()
    if last_close >= average_close:
        return "Bullish"
    else:
        return "Bearish"


# Read the Kivy file that we made for the GUI.
Builder.load_file('stock.kv')


class MainScreen(Screen):

    # Display the png we made with the png method.
    def show_png(self):
        stock = self.manager.current_screen.ids.ticker.text
        today = datetime.datetime.today()
        three_month = date.today() + relativedelta(months=-3)
        three_weeks = date.today() + relativedelta(days=-21)
        stock_info = StockInfo(yf.Ticker(stock), three_month, today,
                               yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Open'],
                               yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Close'],
                               yf.Ticker(stock).history(period='1d', start=three_month, end=today)['High'],
                               yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Low'],
                               yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Volume'])
        three_month_calculations = StockInfo(yf.Ticker(stock), three_month, today,
                                             yf.Ticker(stock).history(period='1d', start=three_month, end=today)[
                                                 'Open'],
                                             yf.Ticker(stock).history(period='1d', start=three_month, end=today)[
                                                 'Close'],
                                             yf.Ticker(stock).history(period='1d', start=three_month, end=today)[
                                                 'High'],
                                             yf.Ticker(stock).history(period='1d', start=three_month, end=today)['Low'],
                                             yf.Ticker(stock).history(period='1d', start=three_month, end=today)[
                                                 'Volume'])
        three_week_calculations = StockInfo(yf.Ticker(stock), three_weeks, today,
                                            yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['Open'],
                                            yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)[
                                                'Close'],
                                            yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['High'],
                                            yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)['Low'],
                                            yf.Ticker(stock).history(period='1d', start=three_weeks, end=today)[
                                                'Volume'])
        stock_info.png(title=stock, rsi=three_week_calculations.rsi(), mfi=three_week_calculations.mfi(),
                       imi=three_week_calculations.imi(), sma=three_month_calculations.sma(window_size=3),
                       ss=three_week_calculations.stock_strength(rsi=three_week_calculations.rsi(),
                                                                 mfi=three_week_calculations.mfi(),
                                                                 imi=three_week_calculations.imi(),
                                                                 sma=three_month_calculations.sma(window_size=3)))
        # Display the png and reload the image over the previous one.
        self.manager.current_screen.ids.img.source = 'StockInfo.png'
        self.manager.current_screen.ids.img.reload()


class RootWidget(ScreenManager):
    pass


class StockApp(App):

    def build(self):
        return RootWidget()


# Run the app
if __name__ == '__main__':
    StockApp().run()
