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
def reporteHtml(data_base=pd.DataFrame(),data_activos=pd.DataFrame(),data_vehiculos=pd.DataFrame(),mapwidth=600,mapheight=200):
    
    #-------------------------------------------------------------------------#
    # Header
    html_header = ""
    if not data_base.empty:
        formato = [{'texto':'Total registros','value':int(len(data_base))},
                   {'texto':'Registros únicos','value':int(len(data_base[data_base['ID'].notnull()]['ID'].unique()))},]
        html_paso = ""
        for i in formato:
            if i['value'] is not None:
                value      = '{:,.0f}'.format(i['value'])
                html_paso += f"""
                <div class="col-12 col-md-12 mb-3">
                    <div class="card card-stats card-round">
                        <div class="card-body">
                            <div class="row align-items-center">
                                <div class="col col-stats ms-3 ms-sm-0">
                                    <div class="numbers">
                                        <h4 class="card-title">{value}</h4>
                                        <p class="card-category">{i['texto']}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
        if html_paso!="":
            html_header = f"""
            <div class="row">  
                {html_paso}
            </div>
            """
    
            
    formato        = []
    html_activos = ""
    if not data_activos.empty:
        formato.append({'texto':'Tienen propiedades','value':int(len(data_activos['C.C.'].unique()))})
        
    if not data_vehiculos.empty:
        formato.append({'texto':'Tienen vehículos','value':int(len(data_vehiculos['C.C.'].unique()))})
        
    if not data_activos.empty and not data_vehiculos.empty:
        v1 = data_activos.copy()
        v2 = data_vehiculos.copy()
        v1 = v1[['C.C.']]
        v2 = v2[['C.C.']]
        v1['id1'] = 1
        v2['id2'] = 1
        v         = v1.merge(v2,on='C.C.',how='outer')
        v         = v[(v['id1']==1) & (v['id2']==1)]
        formato.append({'texto':'Tienen propiedades y vehiculos','value':int(len(v['C.C.'].unique()))})
        
        
    if not data_activos.empty:
        data_activos['valormt2'] = data_activos['Avaluo Catastral']/data_activos['areaconstruida']
        value = data_activos['valormt2'].median()
        #value = f"${value:,.0f} m²" 
        formato.append({'texto':'Valor promedio por mt2 avalúo catastral','value':value})
   
    if isinstance(formato,list) and formato!=[]: 
        html_paso = ""
        for i in formato:
            if i['value'] is not None:
                value      = '{:,.0f}'.format(i['value'])
                html_paso += f"""
                <div class="col-12 col-md-12 mb-3">
                    <div class="card card-stats card-round">
                        <div class="card-body">
                            <div class="row align-items-center">
                                <div class="col col-stats ms-3 ms-sm-0">
                                    <div class="numbers">
                                        <h4 class="card-title">{value}</h4>
                                        <p class="card-category">{i['texto']}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
        if html_paso!="":
            html_activos = f"""
            <div class="row">  
                {html_paso}
            </div>
            """
            

    style = """
    <style>
        body, html {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .card {
            --bs-card-spacer-y: 1rem;
            --bs-card-spacer-x: 1rem;
            --bs-card-title-spacer-y: 0.5rem;
            --bs-card-title-color: #000;
            --bs-card-subtitle-color: #6c757d;
            --bs-card-border-width: 1px;
            --bs-card-border-color: rgba(0, 0, 0, 0.125);
            --bs-card-border-radius: 0.25rem;
            --bs-card-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --bs-card-inner-border-radius: calc(0.25rem - 1px);
            --bs-card-cap-padding-y: 0.5rem;
            --bs-card-cap-padding-x: 1rem;
            --bs-card-cap-bg: rgba(0, 123, 255, 0.03);
            --bs-card-cap-color: #007bff;
            --bs-card-height: auto;
            --bs-card-color: #000;
            --bs-card-bg: #fff;
            --bs-card-img-overlay-padding: 1rem;
            --bs-card-group-margin: 0.75rem;
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: var(--bs-card-height);
            color: var(--bs-card-color);
            word-wrap: break-word;
            background-color: var(--bs-card-bg);
            background-clip: border-box;
            border: var(--bs-card-border-width) solid var(--bs-card-border-color);
            border-radius: var(--bs-card-border-radius);
            box-shadow: var(--bs-card-box-shadow);
        }

        .card-stats .icon-big {
            font-size: 3rem;
            line-height: 1;
            color: #fff;
        }

        .card-stats .icon-primary {
            background-color: #007bff;
        }

        .bubble-shadow-small {
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            border-radius: 50%;
            padding: 1rem;
        }

        .card-stats .numbers {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        .card-stats .card-category {
            color: #6c757d;
            font-size: 0.8rem;
            margin: 0;
            text-align: center;
        }

        .card-stats .card-title {
            margin: 0;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
        }
        
        .small-text {
            font-size: 0.3rem; 
            color: #6c757d; 
        }
        .graph-container {
            width: 100%;
            height: 100%;
            margin-bottom: 0;
        }
        
        .card-custom {
            height: 215px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .card-body-custom {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }
        
        .image-container img {
            width: 100%;
            height: auto;
            border-radius: 0.25rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
    </style>
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visitors Card</title>
        <!-- Incluyendo Bootstrap CSS para el diseño de las tarjetas -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css">
        <!-- Font Awesome para los íconos -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        {style}
    </head>
    <body>
        <div class="container-fluid">
            {html_header}
            {html_activos}
        </div>
    </body>
    </html>
    """
    return html

@st.cache_data(show_spinner=False)
def reporteHtmlSelect(data_base=pd.DataFrame(),data_activos=pd.DataFrame(),data_vehiculos=pd.DataFrame(),mapwidth=600,mapheight=200):
    
    #-------------------------------------------------------------------------#
    # Header            
    formato        = []
    html_activos = ""
    if not data_activos.empty:
        formato.append({'texto':'Propiedades en Bogotá','value':int(len(data_activos))})
        formato.append({'texto':'Valor de las propiedades','value':data_activos['Avaluo Catastral'].sum()})
    else:
        formato.append({'texto':'','value':'No tiene propiedades en Bogotá'})
        
    if not data_activos.empty:
        data_activos['valormt2'] = data_activos['Avaluo Catastral']/data_activos['areaconstruida']
        value = data_activos['valormt2'].median()
        #value = f"${value:,.0f} m²" 
        formato.append({'texto':'Valor promedio por mt2 avalúo catastral','value':value})
   
    if not data_activos.empty and not data_vehiculos.empty:
        v1 = data_activos.copy()
        v2 = data_vehiculos.copy()
        v1 = v1[['C.C.']]
        v2 = v2[['C.C.']]
        v1['id1'] = 1
        v2['id2'] = 1
        v         = v1.merge(v2,on='C.C.',how='outer')
        v         = v[(v['id1']==1) & (v['id2']==1)]
        if not v.empty:
            formato.append({'texto':'','value':'Tiene propiedades y vehiculos'})
      

    if not data_vehiculos.empty:
        formato.append({'texto':'Vehículos','value':int(len(data_vehiculos))})
    else: 
        formato.append({'texto':'','value':'No tiene vehículos'})

    if isinstance(formato,list) and formato!=[]: 
        html_paso = ""
        for i in formato:
            try:    value = '{:,.0f}'.format(i['value'])
            except: value = i['value']
            html_paso += f"""
            <div class="col-12 col-md-12 mb-3">
                <div class="card card-stats card-round">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col col-stats ms-3 ms-sm-0">
                                <div class="numbers">
                                    <h4 class="card-title">{value}</h4>
                                    <p class="card-category">{i['texto']}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        if html_paso!="":
            html_activos = f"""
            <div class="row">  
                {html_paso}
            </div>
            """
            

    style = """
    <style>
        body, html {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .card {
            --bs-card-spacer-y: 1rem;
            --bs-card-spacer-x: 1rem;
            --bs-card-title-spacer-y: 0.5rem;
            --bs-card-title-color: #000;
            --bs-card-subtitle-color: #6c757d;
            --bs-card-border-width: 1px;
            --bs-card-border-color: rgba(0, 0, 0, 0.125);
            --bs-card-border-radius: 0.25rem;
            --bs-card-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --bs-card-inner-border-radius: calc(0.25rem - 1px);
            --bs-card-cap-padding-y: 0.5rem;
            --bs-card-cap-padding-x: 1rem;
            --bs-card-cap-bg: rgba(0, 123, 255, 0.03);
            --bs-card-cap-color: #007bff;
            --bs-card-height: auto;
            --bs-card-color: #000;
            --bs-card-bg: #fff;
            --bs-card-img-overlay-padding: 1rem;
            --bs-card-group-margin: 0.75rem;
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: var(--bs-card-height);
            color: var(--bs-card-color);
            word-wrap: break-word;
            background-color: var(--bs-card-bg);
            background-clip: border-box;
            border: var(--bs-card-border-width) solid var(--bs-card-border-color);
            border-radius: var(--bs-card-border-radius);
            box-shadow: var(--bs-card-box-shadow);
        }

        .card-stats .icon-big {
            font-size: 3rem;
            line-height: 1;
            color: #fff;
        }

        .card-stats .icon-primary {
            background-color: #007bff;
        }

        .bubble-shadow-small {
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            border-radius: 50%;
            padding: 1rem;
        }

        .card-stats .numbers {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        .card-stats .card-category {
            color: #6c757d;
            font-size: 0.8rem;
            margin: 0;
            text-align: center;
        }

        .card-stats .card-title {
            margin: 0;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
        }
        
        .small-text {
            font-size: 0.3rem; 
            color: #6c757d; 
        }
        .graph-container {
            width: 100%;
            height: 100%;
            margin-bottom: 0;
        }
        
        .card-custom {
            height: 215px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .card-body-custom {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }
        
        .image-container img {
            width: 100%;
            height: auto;
            border-radius: 0.25rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
    </style>
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visitors Card</title>
        <!-- Incluyendo Bootstrap CSS para el diseño de las tarjetas -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css">
        <!-- Font Awesome para los íconos -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        {style}
    </head>
    <body>
        <div class="container-fluid">
            {html_activos}
        </div>
    </body>
    </html>
    """
    return html


@st.cache_data(show_spinner=False)
def reporteHtmlGraficas(data_base=pd.DataFrame(),data_activos=pd.DataFrame(),data_vehiculos=pd.DataFrame(),mapwidth=600,mapheight=200):

    #-------------------------------------------------------------------------#
    # Tiplogias
    html_tipologias = ""
    html_grafica    = ""
    if not data_activos.empty:
        formato = [{'variable':'areaconstruida' ,'titulo':'Distribución por Área Privada'}]
        for iiter in formato:
            variable = iiter['variable']
            titulo   = iiter['titulo']
            df         = data_activos.copy()
            df         = df[df[variable]>0]
            
            if not df.empty:
                df['isin'] = 1
                q1         = df.groupby('isin')[variable].quantile(0.25).reset_index()
                q1.columns = ['isin','q1']
                q3         = df.groupby('isin')[variable].quantile(0.75).reset_index()
                q3.columns = ['isin','q3']
                
                # Remover outliers
                w         = q1.merge(q3,on='isin',how='outer')
                w['iqr']  = w['q3']-w['q1']
                w['linf'] = w['q1'] - 1.5*w['iqr']
                w['lsup'] = w['q3'] + 1.5*w['iqr']
                #w['linf'] = df[variable].min()
                #w['lsup'] = df[variable].max()
                df        = df.merge(w[['isin','linf','lsup']],on='isin',how='left',validate='m:1')
                df        = df[(df[variable]>=df['linf']) & (df[variable]<=df['lsup'])]
                
                w         = df.groupby('isin')['id'].count().reset_index() 
                w.columns = ['isin','count']
                df        = df.merge(w,on='isin',how='left',validate='m:1')
                df        = df[df['count']>2]
        
            if not df.empty:
                fig = px.box(df,x='isin',y=variable,title=titulo,color_discrete_sequence=['#624CAB'])
                fig.update_layout(
                    title_x=0.55,
                    height=int(mapheight),
                    width=int(mapwidth*0.6*0.35),
                    xaxis_title=None,
                    yaxis_title=None,
                    margin=dict(l=80, r=0, t=20, b=0),
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    title_font=dict(size=11, color='black')
                )
                fig.update_xaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
                fig.update_yaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
                fig.update_traces(boxpoints=False)
                html_fig_paso = fig.to_html(config={'displayModeBar': False})
                try:
                    soup = BeautifulSoup(html_fig_paso, 'html.parser')
                    soup = soup.find('body')
                    soup = str(soup.prettify())
                    soup = soup.replace('<body>', '<div style="width: 100%; height: 100%;margin-bottom: 0px;">').replace('</body>', '</div>')
                    html_grafica += f""" 
                    <div class="col-3">
                        <div class="card card-stats card-round card-custom">
                            <div class="card-body card-body-custom">
                                <div class="row align-items-center">
                                    <div class="col col-stats ms-3 ms-sm-0">
                                        <div class="graph-container">
                                            {soup}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                except: pass
            
    if not data_vehiculos.empty and 'modelo' in data_vehiculos:
        df         = data_vehiculos.copy()
        df['id']   = 1
        df         = df.groupby('modelo')['id'].count().reset_index()
        df.columns = ['variable','conteo']
        df         = df.sort_values(by='conteo',ascending=False)
        category_order = df['variable'].tolist()
        
        fig = px.pie(df, names="variable", values="conteo", title='Modelo',color_discrete_sequence=px.colors.sequential.RdBu[::-1],category_orders={"variable": category_order})
        fig.update_traces(textinfo='percent+label',textfont_color='white',textposition='inside')
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',  
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'legend':dict(bgcolor='rgba(0, 0, 0, 0)'),
            'height': 200, 
            'width': int(mapwidth*0.2),
            'margin': dict(l=20, r=0, t=20, b=0),
            'title_font': dict(size=11, color='black'),
        })
        fig.update_traces(textinfo='percent+label', textfont_color='white',textposition='inside',)
        fig.update_xaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_yaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_layout(legend=dict(font=dict(color='black')))

        html_fig_paso = fig.to_html(config={'displayModeBar': False})
        try:
            soup = BeautifulSoup(html_fig_paso, 'html.parser')
            soup = soup.find('body')
            soup = str(soup.prettify())
            soup = soup.replace('<body>', '<div style="width: 100%; height: 100%;margin-bottom: 0px;">').replace('</body>', '</div>')
            html_grafica += f""" 
            <div class="col-3">
                <div class="card card-stats card-round card-custom">
                    <div class="card-body card-body-custom">
                        <div class="row align-items-center">
                            <div class="col col-stats ms-3 ms-sm-0">
                                <div class="graph-container">
                                    {soup}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        except: pass
    
    if not data_vehiculos.empty and 'marca' in data_vehiculos:
        df         = data_vehiculos.copy()
        df['id']   = 1
        df         = df.groupby('marca')['id'].count().reset_index()
        df.columns = ['variable','conteo']
        df         = df.sort_values(by='conteo',ascending=False)
        category_order = df['variable'].tolist()
        
        fig = px.pie(df, names="variable", values="conteo", title='Marca',color_discrete_sequence=px.colors.sequential.RdBu[::-1],category_orders={"variable": category_order})
        fig.update_traces(textinfo='percent+label',textfont_color='white',textposition='inside')
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',  
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'legend':dict(bgcolor='rgba(0, 0, 0, 0)'),
            'height': 200, 
            'width': int(mapwidth*0.2),
            'margin': dict(l=20, r=0, t=20, b=0),
            'title_font': dict(size=11, color='black'),
        })
        fig.update_traces(textinfo='percent+label', textfont_color='white',textposition='inside',)
        fig.update_xaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_yaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_layout(legend=dict(font=dict(color='black')))

        html_fig_paso = fig.to_html(config={'displayModeBar': False})
        try:
            soup = BeautifulSoup(html_fig_paso, 'html.parser')
            soup = soup.find('body')
            soup = str(soup.prettify())
            soup = soup.replace('<body>', '<div style="width: 100%; height: 100%;margin-bottom: 0px;">').replace('</body>', '</div>')
            html_grafica += f""" 
            <div class="col-3">
                <div class="card card-stats card-round card-custom">
                    <div class="card-body card-body-custom">
                        <div class="row align-items-center">
                            <div class="col col-stats ms-3 ms-sm-0">
                                <div class="graph-container">
                                    {soup}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        except: pass

    if not data_vehiculos.empty and 'capacidad personas' in data_vehiculos:
        df         = data_vehiculos.copy()
        df['id']   = 1
        df         = df.groupby('capacidad personas')['id'].count().reset_index()
        df.columns = ['variable','conteo']
        df         = df.sort_values(by='variable',ascending=False)
        category_order = df['variable'].tolist()
        
        fig = px.pie(df, names="variable", values="conteo", title='Número de personas',color_discrete_sequence=px.colors.sequential.RdBu[::-1],category_orders={"variable": category_order})
        fig.update_traces(textinfo='percent+label',textfont_color='white',textposition='inside')
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',  
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'legend':dict(bgcolor='rgba(0, 0, 0, 0)'),
            'height': 200, 
            'width': int(mapwidth*0.2),
            'margin': dict(l=20, r=0, t=20, b=0),
            'title_font': dict(size=11, color='black'),
        })
        fig.update_traces(textinfo='percent+label', textfont_color='white',textposition='inside',)
        fig.update_xaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_yaxes(showgrid=False, zeroline=False,tickfont=dict(color='black'))
        fig.update_layout(legend=dict(font=dict(color='black')))

        html_fig_paso = fig.to_html(config={'displayModeBar': False})
        try:
            soup = BeautifulSoup(html_fig_paso, 'html.parser')
            soup = soup.find('body')
            soup = str(soup.prettify())
            soup = soup.replace('<body>', '<div style="width: 100%; height: 100%;margin-bottom: 0px;">').replace('</body>', '</div>')
            html_grafica += f""" 
            <div class="col-3">
                <div class="card card-stats card-round card-custom">
                    <div class="card-body card-body-custom">
                        <div class="row align-items-center">
                            <div class="col col-stats ms-3 ms-sm-0">
                                <div class="graph-container">
                                    {soup}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        except: pass
    
    if html_grafica!="":
        html_tipologias = f"""
        <div class="row">
            {html_grafica}
        </div>
        """


    style = """
    <style>
        body, html {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .card {
            --bs-card-spacer-y: 1rem;
            --bs-card-spacer-x: 1rem;
            --bs-card-title-spacer-y: 0.5rem;
            --bs-card-title-color: #000;
            --bs-card-subtitle-color: #6c757d;
            --bs-card-border-width: 1px;
            --bs-card-border-color: rgba(0, 0, 0, 0.125);
            --bs-card-border-radius: 0.25rem;
            --bs-card-box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --bs-card-inner-border-radius: calc(0.25rem - 1px);
            --bs-card-cap-padding-y: 0.5rem;
            --bs-card-cap-padding-x: 1rem;
            --bs-card-cap-bg: rgba(0, 123, 255, 0.03);
            --bs-card-cap-color: #007bff;
            --bs-card-height: auto;
            --bs-card-color: #000;
            --bs-card-bg: #fff;
            --bs-card-img-overlay-padding: 1rem;
            --bs-card-group-margin: 0.75rem;
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: var(--bs-card-height);
            color: var(--bs-card-color);
            word-wrap: break-word;
            background-color: var(--bs-card-bg);
            background-clip: border-box;
            border: var(--bs-card-border-width) solid var(--bs-card-border-color);
            border-radius: var(--bs-card-border-radius);
            box-shadow: var(--bs-card-box-shadow);
        }

        .card-stats .icon-big {
            font-size: 3rem;
            line-height: 1;
            color: #fff;
        }

        .card-stats .icon-primary {
            background-color: #007bff;
        }

        .bubble-shadow-small {
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            border-radius: 50%;
            padding: 1rem;
        }

        .card-stats .numbers {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        .card-stats .card-category {
            color: #6c757d;
            font-size: 0.8rem;
            margin: 0;
            text-align: center;
        }

        .card-stats .card-title {
            margin: 0;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
        }
        
        .small-text {
            font-size: 0.3rem; 
            color: #6c757d; 
        }
        .graph-container {
            width: 100%;
            height: 100%;
            margin-bottom: 0;
        }
        
        .card-custom {
            height: 215px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .card-body-custom {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }
        
        .image-container img {
            width: 100%;
            height: auto;
            border-radius: 0.25rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
    </style>
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visitors Card</title>
        <!-- Incluyendo Bootstrap CSS para el diseño de las tarjetas -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css">
        <!-- Font Awesome para los íconos -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        {style}
    </head>
    <body>
        <div class="container-fluid">
            {html_tipologias}
        </div>
    </body>
    </html>
    """
    return html

@st.cache_data(show_spinner=False)
def getdata():
    
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

    return data_base,data_activos,data_vehiculos,data_lasttrans,data_anotaciones

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

if __name__ == "__main__":
    main()