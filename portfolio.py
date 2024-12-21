#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as numpy
import datetime as dt
import yfinance as yf
import financedatabase as fd


# In[2]:


import pandas as pd


# In[3]:


def load_data():
    ticker_list = pd.concat([fd.ETFs().select().reset_index()[['symbol', 'name']],
                             fd.Equities().select().reset_index()[['symbol','name']]])
    ticker_list = ticker_list[ticker_list.symbol.notna()]
    ticker_list['symbol_name'] = ticker_list.symbol + ' - ' + ticker_list.name
    return ticker_list


# In[4]:


ticker_list = load_data()


# In[ ]:




