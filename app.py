import streamlit as st
import yfinance as yf
import datetime as dt
import numpy as np
import pandas as pd

from importnb import Notebook

with Notebook():
    from portfolio import ticker_list

import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Portfolio")

with st.sidebar:
    sel_tickers = st.multiselect('Portfolio Builder', placeholder = "Search Tickers",
                                 options = ticker_list.symbol_name)
    sel_tickers_list = ticker_list[ticker_list.symbol_name.isin(sel_tickers)].symbol

    cols = st.columns(4)
    for i , ticker in enumerate(sel_tickers_list):
        
        cols[i % 4].subheader(ticker)

    
    cols = st.columns(2)
    sel_dt1 = cols[0].date_input('Start Date', value = dt.datetime(2024, 1, 1), format = 'YYYY-MM-DD')
    sel_dt2 = cols[1].date_input('End Date', format='YYYY-MM-DD')

    

    if len(sel_tickers) != 0:
        yfdata = yf.download(list(sel_tickers_list), start=sel_dt1, end=sel_dt2)['Close'].reset_index().melt(id_vars = ['Date'], var_name = 'ticker', value_name='price')
        yfdata['price_start'] = yfdata.groupby('ticker').price.transform('first')
        yfdata['price_pct_daily'] = yfdata.groupby('ticker').price.pct_change()
        yfdata['price_pct'] = (yfdata.price - yfdata.price_start) / yfdata.price_start
        
     




tab1, tab2, tab3= st.tabs(['Index Comparison', 'Portfolio', 'Calculator'])

if len(sel_tickers) == 0:
    st.info('Select tickers to view plots')
else:
    st.empty()
    with tab1:

        data = yf.download(list(sel_tickers_list), start= sel_dt1)
        if 'Adj Close' in data.columns:
            data = data['Adj Close']
        else:
            data = data['Close']        
        retdf = data.pct_change()
        cumulative = (retdf + 1).cumprod() - 1
        pfcumulative = cumulative.mean(axis=1)
        w = (np.ones(len(retdf.cov()))/len(retdf.cov()))
        pfsd = (w.dot(retdf.cov()).dot(w)) ** (1/2)

        st.subheader("Portfolio Risk:")
        pfsd

        snp = yf.download('^GSPC', start=sel_dt1)
        snp = snp['Adj Close'] if 'Adj Close' in snp.columns else snp['Close']
        snpret = snp.pct_change()
        snpdev = (snpret+1).cumprod()-1
        st.subheader("Index Comparison (S&P500)")
        tog = pd.concat([snpdev, pfcumulative], axis=1)
        tog.columns = ['S&P500', 'Portfolio']
        st.line_chart(data=tog)


    with tab2:
        
        st.subheader('All Stocks')
        fig = px.line(yfdata, x='Date', y='price_pct', color='ticker', markers = True)
        fig.add_hline(y=0, line_dash='dash', line_color = "white")
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        fig.update_yaxes(tickformat=',.0%')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Individual Stocks')
        cols = st.columns(3)
        for i, ticker in enumerate(sel_tickers_list):

            cols2 = cols[i % 3].columns(3)
            ticker = 'Close' if len(sel_tickers_list) == 1 else ticker
            cols2[0].metric(label='50 Day Average', value=round(yfdata[yfdata.ticker == ticker].price.tail(50).mean(),2))
            cols2[0].metric(label='1 Year Low', value=round(yfdata[yfdata.ticker == ticker].price.tail(365).min(),2))
            cols2[0].metric(label='1 Year High', value=round(yfdata[yfdata.ticker == ticker].price.tail(365).max(),2))

            fig = px.line(
                    yfdata[yfdata.ticker == ticker], 
                    x='Date', 
                    y='price', 
                    markers=True
                    )            
            fig.update_layout(xaxis_title = None, yaxis_title=None)
            cols[i % 3].plotly_chart(fig, use_container_width=True)

    with tab3:
        cols_tab2 = st.columns((0.2,0.8))
        total = 0
        amounts = {}
        for i, ticker in enumerate(sel_tickers_list):
            cols = cols_tab2[0].columns((0.2,0.3))

            try:
                cols[0].image('https://logo.clearbit.com/' + yf.Ticker(ticker).info['website'].replace('https://www.',''), width=65)
            except:
                cols[i % 4].subheader(ticker)
            amount = cols[1].number_input('', key=ticker, step=50)
            total = total + amount
            amounts[ticker] = amount

        cols_tab2[1].subheader('Total Investment: ' + str(total))
        cols_goal = cols_tab2[1].columns((0.15, 0.20, 0.7))
        cols_goal[0].text('')
        cols_goal[0].subheader('Goal: ')
        goal = cols_goal[1].number_input('', key='goal', step=50)

        df = yfdata.copy()
        df['amount'] = df.ticker.map(amounts) * ( 1 + df.price_pct)

        dfsum = df.groupby('Date').amount.sum().reset_index()
        fig = px.area(df, x ='Date', y = 'amount', color = 'ticker')
        fig.add_hline(y=goal, line_color = 'rgb(57,255,20)', line_dash='dash', line_width = 3)
        if dfsum[dfsum.amount >= goal].shape[0] == 0:
            cols_tab2[1].warning("Goal cannot be reached within this time")
        else:
            fig.add_vline(x=dfsum[dfsum.amount >= goal].Date.iloc[0], line_color='rgb(57,255,20)', line_dash='dash', line_width=3)
            fig.add_trace(go.Scatter(x=[dfsum[dfsum.amount >= goal].Date.iloc[0] + dt.timedelta(days=7)], y=[goal*1.1],
                                     text=[dfsum[dfsum.amount >= goal].Date.dt.date.iloc[0]],
                                     mode = 'text',
                                     name = "Goal",
                                     textfont = dict(color = 'rgb(57,255,20)',
                                                     size = 20)))
        fig.update_layout(xaxis_title = None, yaxis_title=None)
        cols_tab2[1].plotly_chart(fig, use_container_width=True)
        

