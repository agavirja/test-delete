import streamlit as st
from random import random
import folium
from streamlit_folium import st_folium


def create_marker():
    random_lat = (0.5 - random()) + st.session_state.map_config["center"][0]
    random_lon = (0.5 - random()) + st.session_state.map_config["center"][1]

    return folium.Marker(
        location=[random_lat, random_lon],
        popup=f"Random marker at {random_lat:.2f}, {random_lon:.2f}",
    )


@st.cache_data
def base_map():
    m = folium.Map(
        location=st.session_state.map_config["center"],
        zoom_start=st.session_state.map_config["zoom"],
    )
    fg = folium.FeatureGroup(name="Markers")

    return m, fg


@st.experimental_fragment(run_every=0.5)
def draw_map():
    m, fg = base_map()

    for marker in st.session_state["markers"]:
        fg.add_child(marker)

    st_folium(
        m,
        feature_group_to_add=fg,
        center=st.session_state.map_config["center"],
        zoom=st.session_state.map_config["zoom"],
        key="user-map",
        returned_objects=[],
        use_container_width=True,
        height=300,
    )


def add_random_marker():
    st.session_state["markers"].append(create_marker())


def main():
    st.set_page_config(layout="wide")

    if "markers" not in st.session_state:
        st.session_state["markers"] = []

    if "map_config" not in st.session_state:
        st.session_state.map_config = {"center": [4.62, -74.06], "zoom": 8}

    st.header("Refreshing map", divider="rainbow")
    left_column, right_column = st.columns([1, 2])

    with left_column:
        if st.button("Add random marker"):
            add_random_marker()

        if st.button("Clear markers"):
            st.session_state["markers"].clear()

        if st.toggle("Start adding markers automatically"):
            st.experimental_fragment(add_random_marker, run_every=1.0)()

    with right_column:
        draw_map()


if __name__ == "__main__":
    main()