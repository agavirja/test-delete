import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector as sql
import folium
import time
import plotly.express as px
from sqlalchemy import create_engine, types
from streamlit_folium import st_folium
from bs4 import BeautifulSoup
from shapely.geometry import Point

st.set_page_config(layout="wide")


def main():
    mapwidth = 1900
    height   = 500
    
    formato = {
               'delay':0,
               }

    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
            
    col1, col2, col3 = st.columns([6,1,1])
    with col2:
        st.image('https://ingeurbe.com/wp-content/uploads/elementor/thumbs/LOGO-39-ANOS_v2_ing-1-1-qtuw7n0byqtxcj89rf8jqp43j6zlaj8lx4y9j36ups.png', width=400)

    with st.spinner('Cargando información'):
        data_base, data_activos, data_vehiculos, data_lasttrans, data_anotaciones = getdata()


    if data_base is not None:
        col1, col2 = st.columns(2)
        with col2:
            if st.session_state.delay==0:
                draw_map0()
                st.session_state.delay = 1
                st.rerun()
            else:
                draw_map(data_activos)
            
                

@st.cache_data(show_spinner=False)
def getdata():
    try:
        user     = st.secrets["user_bigdata"]
        password = st.secrets["password_bigdata"]
        host     = st.secrets["host_bigdata_lectura"]
        engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/urbex')
        
        data_base        = pd.read_sql_query("SELECT * FROM  urbex.ingeurbe_data_base" , engine)
        data_activos     = pd.read_sql_query("SELECT * FROM  urbex.ingeurbe_data_activos" , engine)
        data_vehiculos   = pd.read_sql_query("SELECT * FROM  urbex.ingeurbe_data_vehiculos" , engine)
        data_lasttrans   = pd.read_sql_query("SELECT * FROM  urbex.ingeurbe_data_lasttrans" , engine)
        data_anotaciones = pd.read_sql_query("SELECT * FROM  urbex.ingeurbe_data_anotaciones" , engine)
        engine.dispose()
        return data_base, data_activos, data_vehiculos, data_lasttrans, data_anotaciones
    except:
        return None, None, None, None, None

@st.cache_data(show_spinner=False)
def geopoints(data):
    if data is None or data.empty:
        return pd.DataFrame().to_json()
    
    if 'latitud' in data and 'longitud' in data:
        data = data[(data['latitud'].notnull()) & (data['longitud'].notnull())]
        
    if not data.empty:
        data['geometry'] = data.apply(lambda x: Point(x['longitud'], x['latitud']), axis=1)
        data = gpd.GeoDataFrame(data, geometry='geometry')
        return data.to_json()
    
    return pd.DataFrame().to_json()


@st.fragment
def draw_map(data_activos):
    m = folium.Map(location=[4.687103, -74.058094], zoom_start=12, tiles="cartodbpositron")
    if data_activos is not None and not data_activos.empty:
        datagjson = geopoints(data_activos)
        folium.GeoJson(datagjson, name="geojson").add_to(m)
    mt = st_folium(m, width=1900, height=500)
    return mt

@st.fragment
def draw_map0():
    m = folium.Map(location=[4.687103, -74.058094], zoom_start=12, tiles="cartodbpositron")
    st_folium(m, width=1900, height=500)

if __name__ == "__main__":
    main()