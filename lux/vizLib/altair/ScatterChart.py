from lux.vizLib.altair.AltairChart import AltairChart
import altair as alt 
alt.data_transformers.disable_max_rows()
class ScatterChart(AltairChart):
	"""
	ScatterChart is a subclass of AltairChart that render as a scatter charts.
	All rendering properties for scatter charts are set here.

	See Also
	--------
	altair-viz.github.io
	"""
	def __init__(self,view):
		super().__init__(view)
	def __repr__(self):
		return f"ScatterChart <{str(self.view)}>"
	def initializeChart(self):
		xAttr = self.view.getAttrByChannel("x")[0]
		yAttr = self.view.getAttrByChannel("y")[0]
		xMin = self.view.xMinMax[xAttr.attribute][0]
		xMax = self.view.xMinMax[xAttr.attribute][1]

		yMin = self.view.yMinMax[yAttr.attribute][0]
		yMax = self.view.yMinMax[yAttr.attribute][1]

		chart = alt.Chart(self.data).mark_circle().encode(
		    x=alt.X(xAttr.attribute,scale=alt.Scale(domain=(xMin, xMax)),type=xAttr.dataType),
		    y=alt.Y(yAttr.attribute,scale=alt.Scale(domain=(yMin, yMax)),type=yAttr.dataType)
		)
		chart = chart.configure_mark(tooltip=alt.TooltipContent('encoding')) # Setting tooltip as non-null
		chart = chart.interactive() # Enable Zooming and Panning

		#####################################
		## Constructing Altair Code String ##
		#####################################
		
		self.code += "import altair as alt\n"
		dfname = "df" # TODO: Placeholder (need to read dynamically via locals())
		self.code += f'''
		chart = alt.Chart({dfname}).mark_circle().encode(
		    x=alt.X('{xAttr.attribute}',scale=alt.Scale(domain=({xMin}, {xMax})),type='{xAttr.dataType}'),
		    y=alt.Y('{yAttr.attribute}',scale=alt.Scale(domain=({yMin}, {yMax})),type='{yAttr.dataType}')
		)
		chart = chart.configure_mark(tooltip=alt.TooltipContent('encoding')) # Setting tooltip as non-null
		chart = chart.interactive() # Enable Zooming and Panning
		'''
		return chart 