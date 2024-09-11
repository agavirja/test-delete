import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector as sql
import folium
import plotly.express as px
from sqlalchemy import create_engine , types
from streamlit_folium import st_folium
from bs4 import BeautifulSoup
from shapely.geometry import Point
#from streamlit_js_eval import streamlit_js_eval

st.set_page_config(layout="wide")


def main():
    
    mapwidth = 1900
    height   = 500
    
    col1,col2,col3 = st.columns([6,1,1])
    with col2:
        st.image('https://ingeurbe.com/wp-content/uploads/elementor/thumbs/LOGO-39-ANOS_v2_ing-1-1-qtuw7n0byqtxcj89rf8jqp43j6zlaj8lx4y9j36ups.png',width=400)

    col1,col2 = st.columns(2)
    with st.spinner('Cargando información'):
        data_base,data_activos,data_vehiculos,data_lasttrans,data_anotaciones = getdata()

        with col2:
            m = folium.Map(location=[4.687103, -74.058094], zoom_start=12,tiles="cartodbpositron")
            if not data_activos.empty:
                datagjson = geopoints(data_activos)
                folium.GeoJson(datagjson).add_to(m)
            st_map = st_folium(m,width=int(mapwidth*0.7),height=500)

@st.cache_data(show_spinner=False)
def geopoints(data):
    
    geojson = pd.DataFrame().to_json()
    
    if not data.empty:
        if 'latitud' in data and 'longitud' in data:
            data = data[(data['latitud'].notnull()) & (data['longitud'].notnull())]
            
    if not data.empty:
        data['geometry'] = data.apply(lambda x: Point(x['longitud'],x['latitud']),axis=1)
        data             = gpd.GeoDataFrame(data, geometry='geometry')
        data             = data[['geometry']]
        geojson          = data.to_json()
        
    return geojson

@st.cache_data(show_spinner=False)
def getdata():
    
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/urbex')
    
    data_base        = pd.read_sql_query("SELECT * FROM  schema.data" , engine)
    data_activos     = pd.read_sql_query("SELECT * FROM  schema.data1" , engine)
    data_vehiculos   = pd.read_sql_query("SELECT * FROM  schema.data2" , engine)
    data_lasttrans   = pd.read_sql_query("SELECT * FROM  schema.data3" , engine)
    data_anotaciones = pd.read_sql_query("SELECT * FROM  schema.data4" , engine)

    engine.dispose()

    return data_base,data_activos,data_vehiculos,data_lasttrans,data_anotaciones


if __name__ == "__main__":
    main()