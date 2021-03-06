from lux.luxDataFrame.LuxDataframe import LuxDataFrame
from lux.view.View import View
from lux.executor.PandasExecutor import PandasExecutor
from lux.utils import utils

import pandas as pd
import numpy as np
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from scipy.spatial.distance import euclidean
def interestingness(view:View ,ldf:LuxDataFrame) -> int:
	"""
	Compute the interestingness score of the view.
	The interestingness metric is dependent on the view type.

	Parameters
	----------
	view : View
	ldf : LuxDataFrame

	Returns
	-------
	int
		Interestingness Score
	"""	
	

	if view.data is None:
		raise Exception("View.data needs to be populated before interestingness can be computed. Run Executor.execute(view,ldf).")

	n_dim = 0
	n_msr = 0
	
	filterSpecs = utils.getFilterSpecs(view.specLst)
	viewAttrsSpecs = utils.getAttrsSpecs(view.specLst)

	for spec in viewAttrsSpecs:
		if (spec.attribute!="Record"):
			if (spec.dataModel == 'dimension'):
				n_dim += 1
			if (spec.dataModel == 'measure'):
				n_msr += 1
	n_filter = len(filterSpecs)
	attr_specs = [spec for spec in viewAttrsSpecs if spec.attribute != "Record"]
	dimensionLst = view.getAttrByDataModel("dimension")
	measureLst = view.getAttrByDataModel("measure")

	# Bar Chart
	if (n_dim == 1 and (n_msr == 0 or n_msr==1)):
		if (n_filter == 0):
			return unevenness(view, ldf, measureLst, dimensionLst)
		elif(n_filter==1):
			return deviationFromOverall(view,ldf,filterSpecs,measureLst[0].attribute)
	# Histogram
	elif (n_dim == 0 and n_msr == 1):
		if (n_filter == 0):
			v = view.data["Count of Records"]
			return skewness(v)
		elif (n_filter == 1):
			return deviationFromOverall(view,ldf,filterSpecs,"Count of Records")
	# Scatter Plot
	elif (n_dim == 0 and n_msr == 2):
		if (n_filter==1):
			v_filter_size = getFilteredSize(filterSpecs,view.data)
			v_size = len(view.data)
			sig = v_filter_size/v_size
		else:
			sig = 1
		return sig * monotonicity(view,attr_specs)
	# Scatterplot colored by Dimension
	elif (n_dim == 1 and n_msr == 2):
		colorAttr = view.getAttrByChannel("color")[0].attribute
		
		C = ldf.cardinality[colorAttr]
		if (C<40):
			return 1/C
		else:
			return -1
	# Scatterplot colored by dimension
	elif (n_dim== 1 and n_msr == 2):
		return 0.2
	# Scatterplot colored by measure
	elif (n_msr == 3):
		return 0.1
	# Default
	else:
		return -1
def getFilteredSize(filterSpecs,ldf):
	filter_spec = filterSpecs[0]
	result = PandasExecutor.applyFilter(ldf, filter_spec.attribute, filter_spec.filterOp, filter_spec.value)
	return len(result)
def skewness(v):
	from scipy.stats import skew
	return skew(v)

def deviationFromOverall(view:View,ldf:LuxDataFrame,filterSpecs:list,msrAttribute:str) -> int:
	"""
	Difference in bar chart/histogram shape from overall chart
	Note: this function assumes that the filtered view.data is operating on the same range as the unfiltered view.data. 

	Parameters
	----------
	view : View
	ldf : LuxDataFrame
	filterSpecs : list
		List of filters from the View
	msrAttribute : str
		The attribute name of the measure value of the chart

	Returns
	-------
	int
		Score describing how different the view is from the overall view
	"""	
	v_filter_size = getFilteredSize(filterSpecs,ldf)
	v_size = len(view.data)
	v_filter = view.data[msrAttribute]
	v_filter = v_filter/v_filter.sum() # normalize by total to get ratio

	# Generate an "Overall" View (TODO: This is computed multiple times for every view, alternative is to directly access df.viewCollection but we do not have guaruntee that will always be unfiltered view (in the non-Filter action scenario))
	import copy
	unfilteredView = copy.copy(view)
	unfilteredView.specLst = utils.getAttrsSpecs(view.specLst) # Remove filters, keep only attribute specs
	ldf.executor.execute([unfilteredView],ldf)
	
	v = unfilteredView.data[msrAttribute]
	v = v/v.sum()  
	assert len(v) == len(v_filter), "Data for filtered and unfiltered view have unequal length." 
	sig = v_filter_size/v_size #significance factor
	# Euclidean distance as L2 function
	from scipy.spatial.distance import euclidean
	return sig* euclidean(v, v_filter)

def unevenness(view:View,ldf:LuxDataFrame,measureLst:list,dimensionLst:list) -> int:
	"""
	Measure the unevenness of a bar chart view.
	If a bar chart is highly uneven across the possible values, then it may be interesting. (e.g., USA produces lots of cars compared to Japan and Europe)
	Likewise, if a bar chart shows that the measure is the same for any possible values the dimension attribute could take on, then it may not very informative. 
	(e.g., The cars produced across all Origins (Europe, Japan, and USA) has approximately the same average Acceleration.)

	Parameters
	----------
	view : View
	ldf : LuxDataFrame
	measureLst : list
		List of measures
	dimensionLst : list
		List of dimensions
	Returns
	-------
	int
		Score describing how uneven the bar chart is.
	"""	
	v = view.data[measureLst[0].attribute]
	v = v/v.sum() # normalize by total to get ratio
	C = ldf.cardinality[dimensionLst[0].attribute]
	D = (0.5) ** C # cardinality-based discounting factor
	v_flat = pd.Series([1 / C] * len(v))
	if (is_datetime(v)):
		v = v.astype('int')
	return D * euclidean(v, v_flat) 

def mutual_information(v_x:list , v_y:list) -> int:
	#Interestingness metric for two measure attributes
  	#Calculate maximal information coefficient (see Murphy pg 61) or Pearson's correlation
	from sklearn.metrics import mutual_info_score
	return mutual_info_score(v_x, v_y)

def monotonicity(view:View,attr_specs:list,ignoreIdentity:bool=True) ->int:
	"""
	Monotonicity measures there is a monotonic trend in the scatterplot, whether linear or not.
	This score is computed as the square of the Spearman correlation coefficient, which is the Pearson correlation on the ranks of x and y.
	See "Graph-Theoretic Scagnostics", Wilkinson et al 2005: https://research.tableau.com/sites/default/files/Wilkinson_Infovis-05.pdf
	Parameters
	----------
	view : View
	attr_spec: list
		List of attribute Spec objects

	ignoreIdentity: bool
		Boolean flag to ignore items with the same x and y attribute (score as -1)

	Returns
	-------
	int
		Score describing the strength of monotonic relationship in view
	"""	
	from scipy.stats import spearmanr
	msr1 = attr_specs[0].attribute
	msr2 = attr_specs[1].attribute

	if(ignoreIdentity and msr1 == msr2): #remove if measures are the same
		return -1
	v_x = view.data[msr1]
	v_y = view.data[msr2]
	return (spearmanr(v_x, v_y)[0]) ** 2
	# import scipy.stats
	# return abs(scipy.stats.pearsonr(v_x,v_y)[0])
