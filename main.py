import pandas as pd
import numpy as np
import geopandas as gpd
import panel as pn
import holoviews as hv
import geoviews as gv
import geoviews.feature as gf
from bokeh.models import HoverTool
import hvplot.pandas
import datashader.geo
from geoviews import opts
from holoviews import streams
gv.extension('bokeh')
hv.extension('bokeh')
pn.extension()

'''Sets up Train (country,tempchange), geodf (added polygon geometry to Train), 
centroidf (centre LongLat of all countries), pointsDf (merging Train and centroid)'''

mainDf=pd.read_pickle('NewDf2')
Train=pd.read_csv('tdiff4.csv')
centroidf=pd.read_csv('country_centroids_az8.csv',usecols=['admin','adm0_a3','Longitude', 'Latitude'])
centroidf.rename(mapper={'admin':'country','adm0_a3':'iso3'},inplace=True,axis=1)

shapefile1='ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
gdf1 = gpd.read_file(shapefile1)[['ADMIN', 'ADM0_A3', 'geometry']]
gdf1.columns = ['country', 'country_code', 'geometry']
gdf1.drop(gdf1.index[159],inplace=True)

shapefile='ne_10m_admin_0_sovereignty/ne_10m_admin_0_sovereignty.shp'
gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
gdf.columns = ['country', 'country_code', 'geometry']
gdf.drop(gdf.index[163],inplace=True)
gdf.reset_index().drop('index',axis=1,inplace=True)

gdf.replace(to_replace=gdf.country.loc[188],value='Sao Tome and Principe',inplace=True)

newcntlist=['Greenland','Kazakhstan','New Caledonia','Puerto Rico']
for i in newcntlist:
    shit=gdf1.loc[gdf1.country==i]
    gdf=pd.concat([gdf,shit])

geodf=pd.merge(gdf,Train,on='country')
pointsDf=pd.merge(Train,centroidf,how='left',on='country') # Just so I have only the centroids of countrys on the map
pointsDf.dropna(inplace=True)
pointsDf['easting'], pointsDf['northing'] = datashader.geo.lnglat_to_meters(pointsDf.Longitude, pointsDf.Latitude)

'''Setting up geopolygon and centroid maps'''

tooltips = [
    ('Country', '@country'),
    ('ΔTemp(1901-2012)', '@tempchange')
]
hover = HoverTool(tooltips=tooltips)
geoplot=gv.Polygons(geodf,vdims=['tempchange','country']).opts(width=700,height=350,colorbar=True,color_index='tempchange'\
                                                       ,tools=[hover,'tap'])

pointsplot=pointsDf.hvplot.points(x='easting',y='northing',color='black',size=50).opts(marker='d',tools=['tap'])

'''Creating the dashboard'''

# Main pipeline: extracts the clicked country from the complete Dataframe
def main_pipeline(ds,index):
    if not index:
        return ds.iloc[[]]
    row = pointsplot.data.iloc[index[0]]
    df = ds[ds['iso3']==row.iso3]
    return hv.Dataset(df)

dataset = hv.Dataset(mainDf)
index_stream = streams.Selection1D(source=pointsplot, index=[0])
indicator=pn.widgets.Select(value='country', options=mainDf.columns.tolist())

# This is where it all happens: the mainDf having all data is connected by the points stream thru the apply function
filtered_ds = dataset.apply(main_pipeline, index=index_stream.param.index)

# Creates line plot of temperature for the selected country
def temp_scatter(ds):
    countryname=ds.data['country'].iloc[0]
    return ds.data.hvplot.line('date','Temp(C)',title='{}'.format(countryname))

# Creates the economic/social indicator line plot based on the country & indicator selected by user
@pn.depends(index_stream.param.index, indicator.param.value)
def indplot(index,indicator):
    if not index:
        return pointsplot.iloc[[]]
    streamdf=pointsplot.data.iloc[index[0]]
    df=mainDf[mainDf['iso3']==streamdf.iso3]
    return df.hvplot.line('date','{}'.format(indicator))

# Final adjustments for setting up display
dynamic_scatter=pn.panel(filtered_ds.apply(temp_scatter)) 
econplot=pn.panel(indplot)

gpplot=pn.panel((geoplot*pointsplot).opts(width=700,height=450))
indicatorbox=pn.WidgetBox(indicator)
ecandwid=pn.Column(indicatorbox,econplot)

'''Serving the app'''

pn.Row(gpplot,pn.Column(dynamic_scatter,indicatorbox,econplot)).servable()