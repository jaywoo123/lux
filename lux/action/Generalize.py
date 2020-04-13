import lux
import scipy.stats
import numpy as np
from lux.view.View import View
from lux.compiler.Compiler import Compiler
from lux.executor.PandasExecutor import PandasExecutor
from lux.utils import utils
from lux.interestingness.interestingness import interestingness
# from compiler.Compiler import Compiler
'''
Shows possible visualizations when one attribute or filter from the current context is removed
'''
def generalize(ldf):
	# takes in a dataObject and generates a list of new dataObjects, each with a single measure from the original object removed
	# -->  return list of dataObjects with corresponding interestingness scores

	recommendation = {"action":"Generalize",
						   "description":"Remove one attribute or filter to observe a more general trend."}
	output = []
	excludedColumns = []
	columnSpec = utils.getAttrsSpecs(ldf.context)
	rowSpecs = utils.getFilterSpecs(ldf.context)
	# if we do no have enough column attributes or too many, return no views.
	if(len(columnSpec)<2 or len(columnSpec)>4):
		recommendation["collection"] = []
		return recommendation
	for spec in columnSpec:
		columns = spec.attribute
		if type(columns) == list:
			for column in columns:
				if column not in excludedColumns:
					tempView = View(ldf.context)
					tempView.removeColumnFromSpecNew(column)
					excludedColumns.append(column)
					tempView.score = interestingness(tempView,ldf)
					output.append(tempView)
		elif type(columns) == str:
			if columns not in excludedColumns:
				tempView = View(ldf.context)
				tempView.removeColumnFromSpecNew(columns)
				excludedColumns.append(columns)
				tempView.score = interestingness(tempView,ldf)
		output.append(tempView)
	for i, spec in enumerate(rowSpecs):
		newSpec = ldf.context.copy()
		newSpec.pop(i)
		tempView = View(newSpec)
		tempView.score = interestingness(tempView,ldf)
		output.append(tempView)
		
	vc = lux.view.ViewCollection.ViewCollection(output)
	vc = Compiler.compile(ldf,vc,enumerateCollection=False)
	PandasExecutor.execute(vc,ldf)
	recommendation["collection"] = vc
	return recommendation