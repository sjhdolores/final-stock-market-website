#from .stock import neuralNetwork
# // written by: Yanhao Wang, Jiahui Shan, Mohan Xiao
# // assisted by:  Yanhao Wang, Jiahui Shan, Mohan Xiao
# // debugged by:
# // etc.
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
# from  . import data
# from  . import data1
from datetime import date,datetime
from django.utils import timezone
# Create your views here.
#from .models import Today
from . models import Company
from . import analyzer
import json_, sqlite3
from decimal import Decimal
import retrieve_data_update as rdu
from yahoo_finance import Share
import pandas as pd
import csv,os
import numpy as np
from retrieve_data_update import collect_data, getAllIndicators,getHistoryCSV

company =  {28:['GOOG','Alphabet Inc.'],
			29:['TWTR','Twitter, Inc.'],
			30:['AMZN','Amazon.com, Inc.'],
			31:['FB','Facebook, Inc.'],
			32:['YHOO','Yahoo! Inc.'],
			33:['AAPL', 'Apple Inc.'],
			34:['GPRO', 'Go Pro, Inc.'],
			35:['INTC', 'Intel Corporation'],
			36:['NFLX', 'Netflix, Inc.'],
			37:['TSLA', 'Tesla, Inc.']
		}
stock_list = ['GOOG','TWTR', 'AMZN','FB','YHOO','AAPL','GPRO', 'INTC', 'NFLX', 'TSLA' ]
stock_name = ['Google','Twitter', 'Amazon','Facebook','Yahoo','Apple','Go Pro', 'Intel Corporation', 'Netflix', 'Tesla']

def updateData(request):
	collect_data()
	getAllIndicators()
	getHistoryCSV()
	c_id = 28
	avg, high, low, companies = query(company[c_id][0])
	real_time = rdu.get_realtime_data(stock_list)
	context = {
		'id':c_id,
		'avg':avg,
		'high':high,
		'low':low,
		'companies':companies,
		'real_time':real_time,
		'stock_name':stock_name,
		'company_name':company[c_id]
	}
	return render(request,'home.html',context)

def search(request):
	stock = request.GET.get('put')
	flagvar = 0
	try:
		symbol = Share(stock)
		stock_name = symbol.get_name()
		stock_data = symbol.get_historical('2016-01-01',date.today().strftime("%Y-%m-%d"))
		stock_df = pd.DataFrame(stock_data)
		abbr = stock_df['Symbol'][0]
		temp = pd.DataFrame({'Close_Price':[],'Low':[],'High':[],'Date':[]})
		temp['Date'] = stock_df['Date']
		temp['High'] = stock_df['High']
		temp['Low'] = stock_df['Low']
		temp['Close_Price'] = stock_df['Adj_Close']
		path = os.getcwd()
		filepath = path+os.sep+'static'+os.sep+'js'+os.sep+'search'
		os.chdir(filepath)
		temp.to_csv(filepath+"/result.csv",index_label=False,index=False)
		os.chdir(path)
		flagvar =1
	except:
		flagvar = 0
		abbr = ''
		stock_name=''
	context = {'flag':flagvar,
			'abbr':abbr,
			'stock_name':stock_name}

	return render(request,'search2.html',context)

def searchpage(request):
	return render(request, 'searchpage.html')	 


def sidebar(request,company_id=0):
	vote_up = 0
	vote_down = 0
	vote_hold = 0
	if(company_id==0):

		context={

		}
	else:
		c_id = int (company_id)
		# p = Company.objects.get(pk=company_id)
		# print company[c_id][0]
		pred, last, tomorrow, today = rdu.regression_predict(company[c_id][0]+"_historical",80)
		svm_pred = rdu.svm_predict(company[c_id][0]+'_historical',100)
		svm_pred_long = rdu.svm_predict_long(company[c_id][0]+'_historical',15)
		# print svm_longterm
		ann_pred = rdu.ann_predict(company[c_id][0]+"_historical",100)
		ann_pred_long = rdu.ann_predict_long(company[c_id][0]+"_historical",100)
		pred_long,last_long,tomorrow_long,today_long = rdu.regression_predict_long(company[c_id][0]+"_historical",300)

		if (pred-last>0): 
			delta = 1
		else: 
			delta = 0

		if (pred_long - last>0):
			delta_long = 1
		else:
			delta_long = 0

		vote = 0
		if (ann_pred_long==1):
			vote+=0.56159
		if (ann_pred_long==-1):
			vote_down+=0.56159
		if (ann_pred_long==0):
			vote_hold+=0.56159

		if (ann_pred==1):
			vote_up+=0.583
		if (ann_pred==-1):
			vote_down+=0.583
		if (ann_pred==0):
			vote_hold+=0.583


		if(pred>last):
			vote_up+=0.96
		if(pred==last):
			vote_hold+=0.96
		if(pred<last):
			vote_down+=0.96

		if(pred_long>last):
			vote_up+=0.918
		if(pred_long==last):
			vote_hold+=0.918
		if(pred_long<last):
			vote_down+=0.918

		if (svm_pred==1):
			vote_up+=0.583
		if (svm_pred==-1):
			vote_down+=0.583
		if (svm_pred==0):
			vote_hold+=0.583

		if (svm_pred_long==1):
			vote_up+=0.5999
		if (svm_pred_long==-1):
			vote_down+=0.5999
		if (svm_pred_long==0):
			vote_hold+=0.5999
		context = {
			'company_name':company[c_id],
			'id':c_id,
			'today': today,
			'pred':pred,
			'last':last,
			'tomorrow':tomorrow,
			'delta': delta,
			'svm_pred':svm_pred,
			'ann_pred':ann_pred,
			'pred_long':pred_long,
			'svm_pred_long':svm_pred_long,
			'ann_pred_long':ann_pred_long,
			'delta_long': delta_long,
			# 'suggest': suggest
		}
	path = os.getcwd()
	filepath = path+os.sep+'static'+os.sep+'js'+os.sep+'indicator'
	os.chdir(filepath)
	filename = company[int(company_id)][0]
	#bollinger csv
	b1csvfile = filename+'_bollinger1.csv'
	f = open(b1csvfile)
	lines = f.readlines()[-20:]
	price_col = []
	lower_col = []
	upper_col = []
	vote = 0
	for each in lines:
		each = each.split(',')
		price = float(each[2])
		lower = float(each[3])
		upper = float(each[4][:-1])
		price_col.append(price)
		lower_col.append(lower)
		upper_col.append(upper)
	price_min = min(price_col)
	price_max = max(price_col)
	lower_min = min(lower_col)
	upper_max = max(upper_col)
	if price_max<=lower_min:
		# context['b1_advice'] = 1
		vote_up+=0.4
	elif price_min>=upper_max:
		# context['b1_advice'] = 2
		vote_down+=0.4
	else:
		# context['b1_advice'] = 3
		vote_hold+=0.4
	#rsi csv file
	rsicsvfile = filename+'_rsi.csv'
	f = open(rsicsvfile)
	rsi_var = f.readlines()[-1].split(',')[-1]
	rsi_var = float(rsi_var[:-1])
	if rsi_var<30:
		# context['rsi_advice'] = 1
		vote_up+=0.4
	elif rsi_var>70:
		# context['rsi_advice'] = 2
		vote_down+=0.4
	else:
		# context['rsi_advice'] = 3
		vote_hold += 0.4
	#dmi csv
	dmicsvfile = filename+'_dmi.csv'
	f = open(dmicsvfile)
	line = f.readlines()[-1].split(',')
	ADX = float(line[0])
	DI_minus = float(line[1])
	DI_plus = float(line[2])
	if ADX>25:
		if DI_plus>=DI_minus:
			vote_up+=0.4
		else:
			# context['dmi_advice'] = 2
			vote_down+=0.4
	else:
		vote_hold +=0.4
	suggest = [vote_up, vote_down, vote_hold]
	option = [1, -1, 0]
	suggest = np.argmax(suggest)
	context['suggest'] = option[suggest]
	os.chdir(path)

	return render(request, 'prediction.html', context) 

def homeindex(request,company_id=28):
	if(company_id==0):

		context={

		}
	else:
		c_id = int (company_id)
		# p = Company.objects.get(pk=company_id) 
		avg, high, low, companies = query(company[c_id][0])
		real_time = rdu.get_realtime_data(stock_list)
		context = {
			'id':c_id,
			'avg':avg,
			'high':high,
			'low':low,
			'companies':companies,
			'real_time':real_time,
			'stock_name':stock_name,
			'company_name':company[c_id],
		}
	return render(request, 'home.html', context) 


def sidebarhome(request,company_id=0):
	if(company_id==0):

		context={

		}
	else:
		c_id = int (company_id)
		# p = Company.objects.get(pk=company_id) 
		avg, high, low, companies = query(company[c_id][0])
		real_time = rdu.get_realtime_data(stock_list)
		context = {
			'id':c_id,
			'avg':avg,
			'high':high,
			'low':low,
			'companies':companies,
			'real_time':real_time,
			'stock_name':stock_name,
			'company_name':company[c_id]
		}
	print context
	return render(request, 'home.html', context) 

def indicator(request,company_id=0):
	if(company_id==0):

		context={

		}
	else:
		c_id = int (company_id)
		# p = Company.objects.get(pk=company_id) 
		context = {
			'id':c_id,
			'company_name':company[c_id]
		}
	path = os.getcwd()
	filepath = path+os.sep+'static'+os.sep+'js'+os.sep+'indicator'
	os.chdir(filepath)
	filename = company[int(company_id)][0]
	#bollinger csv
	b1csvfile = filename+'_bollinger1.csv'
	f = open(b1csvfile)
	lines = f.readlines()[-20:]
	price_col = []
	lower_col = []
	upper_col = []
	vote = 0
	for each in lines:
		each = each.split(',')
		price = float(each[2])
		lower = float(each[3])
		upper = float(each[4][:-1])
		price_col.append(price)
		lower_col.append(lower)
		upper_col.append(upper)
	price_min = min(price_col)
	price_max = max(price_col)
	lower_min = min(lower_col)
	upper_max = max(upper_col)
	if price_max<=lower_min:
		context['b1_advice'] = 1
		vote+=1
	elif price_min>=upper_max:
		context['b1_advice'] = 2
		vote-=1
	else:
		context['b1_advice'] = 3
	#rsi csv file
	rsicsvfile = filename+'_rsi.csv'
	f = open(rsicsvfile)
	rsi_var = f.readlines()[-1].split(',')[-1]
	rsi_var = float(rsi_var[:-1])
	if rsi_var<30:
		context['rsi_advice'] = 1
		vote+=1
	elif rsi_var>70:
		context['rsi_advice'] = 2
		vote-=1
	else:
		context['rsi_advice'] = 3
	#dmi csv
	dmicsvfile = filename+'_dmi.csv'
	f = open(dmicsvfile)
	line = f.readlines()[-1].split(',')
	ADX = float(line[0])
	DI_minus = float(line[1])
	DI_plus = float(line[2])
	if ADX>25:
		if DI_plus>=DI_minus:
			context['dmi_advice'] = 1
			vote+=1
		else:
			context['dmi_advice'] = 2
			vote-=1
	else:
		context['dim_advice'] = 3
	if(vote>0):
		suggest = 1
	elif(vote==0):
		suggest = 0
	else:
		suggest = -1
	context['suggest'] = suggest
	os.chdir(path)
	return render(request, 'indicator.html', context) 


def query(name):
	tbl = rdu.get_data_db(name+'_historical')
	avg = rdu.getAverage(tbl)
	low = rdu.getLowest(tbl)
	high = rdu.getHighest(tbl)
	companies = rdu.getCompanies(name+'_historical')
	# print "zhangxin ",companies
	return avg, high, low, companies
