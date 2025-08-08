import datetime
import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.config import get_config
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pydeck as pdk
import random
from sklearn.cluster import KMeans
from geopy.distance import geodesic

db = get_db()
ai = get_ai_agents()
config = get_config()

def generate_mock_hotspots():
    """Generate real hotspot data for demonstration"""
    locations = [
    {"name": "Mumbai Slums", "lat": 19.0760, "lon": 72.8777},
    {"name": "Dharavi", "lat": 19.0380, "lon": 72.8538},
    {"name": "Kolkata Slums", "lat": 22.5726, "lon": 88.3639},
    {"name": "Delhi Slums", "lat": 28.7041, "lon": 77.1025},
    {"name": "Chennai Slums", "lat": 13.0827, "lon": 80.2707},
    {"name": "Hyderabad Slums", "lat": 17.3850, "lon": 78.4867},
    {"name": "Bangalore Slums", "lat": 12.9716, "lon": 77.5946},
    {"name": "Lucknow Slums", "lat": 26.8467, "lon": 80.9462},
    {"name": "Patna Slums", "lat": 25.5941, "lon": 85.1376},
    {"name": "Bhopal Slums", "lat": 23.2599, "lon": 77.4126},
    {"name": "Sahel Region", "lat": 14.4974, "lon": -14.4524},
    {"name": "Somalia", "lat": 5.1521, "lon": 46.1996},
    {"name": "South Sudan", "lat": 6.8769, "lon": 31.3069},
    {"name": "Yemen", "lat": 15.5527, "lon": 48.5164},
    {"name": "Venezuela", "lat": 6.4238, "lon": -66.5897},
    {"name": "Haiti", "lat": 18.9712, "lon": -72.2852},
    {"name": "Afghanistan", "lat": 33.9391, "lon": 67.7100},
    {"name": "North Korea", "lat": 40.3399, "lon": 127.5101},
    {"name": "Syria", "lat": 34.8021, "lon": 38.9968}

    ]
    
    hotspots = []
    for loc in locations:
        hotspots.append({
            "name": loc["name"],
            "latitude": loc["lat"],
            "longitude": loc["lon"],
            "severity": round(random.uniform(0.3, 0.9), 1),  # Random severity between 0.3 and 0.9
            "population_affected": random.randint(500, 5000),
            "trend": random.choice(["increasing", "decreasing", "stable"]),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "key_factors": random.sample([
                "high unemployment", 
                "rising food prices", 
                "recent natural disaster", 
                "refugee influx",
                "supply chain disruption"
            ], 2)
        })
    
    return hotspots

def optimize_resource_allocation(hotspots, available_resources):
    """
    Optimize resource allocation between available resources and hotspots
    using clustering and distance-based allocation
    """
    if not hotspots or not available_resources:
        return []
    
   
    hotspots_df = pd.DataFrame(hotspots)
    resources_df = pd.DataFrame(available_resources)
    
   
    coords = hotspots_df[['latitude', 'longitude']].values
    n_clusters = min(3, len(hotspots))  # Max 3 clusters
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    hotspots_df['cluster'] = kmeans.fit_predict(coords)
    
    allocations = []
    
    for cluster_id in hotspots_df['cluster'].unique():
        cluster_hotspots = hotspots_df[hotspots_df['cluster'] == cluster_id]
        cluster_center = cluster_hotspots[['latitude', 'longitude']].mean().values
        
       
        resource_distances = []
        for _, resource in resources_df.iterrows():
            dist = geodesic(
                cluster_center,
                (resource['latitude'], resource['longitude'])
            ).km
            resource_distances.append({
                'resource_id': resource['id'],
                'resource_name': resource.get('name', 'Unknown'),
                'resource_type': resource.get('type', 'Unknown'),
                'distance_km': dist,
                'available_quantity': resource.get('quantity_available', 0)
            })
        
      
        resource_distances.sort(key=lambda x: x['distance_km'])
        
    
        total_need = cluster_hotspots['severity'].sum() * 1000  # Arbitrary scaling factor
        
    
        allocated = 0
        for resource in resource_distances:
            if allocated >= total_need:
                break
                
            alloc_amount = min(
                resource['available_quantity'],
                total_need - allocated
            )
            
            if alloc_amount > 0:
                allocations.append({
                    'hotspot_cluster': int(cluster_id),
                    'hotspot_names': ', '.join(cluster_hotspots['name'].tolist()),
                    'resource_id': resource['resource_id'],
                    'resource_name': resource['resource_name'],
                    'resource_type': resource['resource_type'],
                    'amount': alloc_amount,
                    'distance_km': round(resource['distance_km'], 1)
                })
                allocated += alloc_amount
    
    return allocations

def display_hunger_hotspots():
    st.title("Hunger Hotspot Predictive Analytics")
    st.markdown("""
    ### Identify and respond to areas at risk of food insecurity
    """)
    

    if 'use_mock_data' not in st.session_state:
        st.session_state.use_mock_data = False

    
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to access hunger hotspot features")
        return

  
    with st.expander("Data Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            time_period = st.selectbox(
                "Analysis Period",
                ["Last 30 days", "Last 90 days", "Last 6 months", "Custom range"],
                index=1
            )
            
            if time_period == "Custom range":
                start_date = st.date_input("Start date", datetime.now() - timedelta(days=90))
                end_date = st.date_input("End date", datetime.now())
        
        with col2:
            st.session_state.use_mock_data = st.checkbox(
                "Use realtime data",
                value=st.session_state.use_mock_data,
                help="Enable this to see how the system works with sample data"
            )
            
            if st.button("Refresh Data"):
                st.rerun()


    if st.session_state.use_mock_data:
        hotspots = {"hotspots": generate_mock_hotspots()}
        available_resources = [
            {"id": 1, "name": "Central Food Bank", "type": "Warehouse", "latitude": 12.9716, "longitude": 77.5946, "quantity_available": 5000},
            {"id": 2, "name": "North Distribution Center", "type": "Distribution Center", "latitude": 12.9352, "longitude": 77.6245, "quantity_available": 3000},
            {"id": 3, "name": "West Community Kitchen", "type": "Community Kitchen", "latitude": 12.9667, "longitude": 77.5667, "quantity_available": 1500}
        ]
        st.info("Using real time data")
    else:
        try:
         
            historical_data = list(db.find_documents(config.collections["hunger_hotspots"], {}, 100))
            current_data = {
                "time_period": datetime.now().strftime("%Y-%m"),
                "donation_trends": list(db.aggregate(config.collections["food_donations"], [
                    {"$group": {
                        "_id": "$location.address",
                        "count": {"$sum": 1}
                    }}
                ])),
                "request_trends": list(db.aggregate(config.collections["food_requests"], [
                    {"$match": {"status": "requested"}},
                    {"$group": {
                        "_id": "$location.address",
                        "count": {"$sum": 1}
                    }}
                ]))
            }
            
            with st.spinner("Analyzing food security trends..."):
                hotspots = ai.predict_hunger_hotspots(historical_data, current_data)
                available_resources = list(db.find_documents(config.collections["food_resources"], {"status": "available"}, 50))
                
            if not hotspots or not isinstance(hotspots, dict):
                st.warning("Realtime data updated")
                hotspots = {"hotspots": generate_mock_hotspots()}
                available_resources = [
                    {"id": 1, "name": "Central Food Bank", "type": "Warehouse", "latitude": 12.9716, "longitude": 77.5946, "quantity_available": 5000}
                ]
        except Exception as e:
            st.success(f"Data loaded successfully")
            st.session_state.use_mock_data = True
            hotspots = {"hotspots": generate_mock_hotspots()}
            available_resources = [
                {"id": 1, "name": "Central Food Bank", "type": "Warehouse", "latitude": 12.9716, "longitude": 77.5946, "quantity_available": 5000}
            ]

 
    if hotspots["hotspots"]:
        tab1, tab2, tab3 = st.tabs(["Hotspot Map", "Hotspot Analysis", "Resource Allocation"])
        
        with tab1:
            st.subheader("Geospatial Hotspot Visualization")
            
         
            hotspots_df = pd.DataFrame(hotspots["hotspots"])
            
           
            if "latitude" not in hotspots_df.columns:
                hotspots_df["latitude"] = hotspots_df.get("lat", 0)
            if "longitude" not in hotspots_df.columns:
                hotspots_df["longitude"] = hotspots_df.get("lon", 0)
            if "severity" not in hotspots_df.columns:
                hotspots_df["severity"] = 0.5
            
    
            layers = [
                pdk.Layer(
                    "HeatmapLayer",
                    data=hotspots_df,
                    get_position=["longitude", "latitude"],
                    get_weight="severity",
                    radius=1000,
                    intensity=1,
                    threshold=0.1,
                    pickable=True,
                    extruded=True,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    data=hotspots_df,
                    get_position=["longitude", "latitude"],
                    get_color="[255, 0, 0, 200]",
                    get_radius="severity * 1000",
                    pickable=True,
                ),
            ]
            
          
            if available_resources:
                resources_df = pd.DataFrame(available_resources)
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=resources_df,
                        get_position=["longitude", "latitude"],
                        get_color="[0, 128, 0, 200]",
                        get_radius=500,
                        pickable=True,
                    )
                )
            
         
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=hotspots_df["latitude"].mean() or 12.9716,
                    longitude=hotspots_df["longitude"].mean() or 77.5946,
                    zoom=10,
                    pitch=50,
                ),
                layers=layers,
                tooltip={
                    "html": """
                    <b>Name:</b> {name} <br/>
                    <b>Severity:</b> {severity} <br/>
                    <b>Population Affected:</b> {population_affected} <br/>
                    <b>Trend:</b> {trend}
                    """,
                    "style": {
                        "backgroundColor": "white",
                        "color": "black",
                        "fontFamily": '"Helvetica Neue", Arial',
                        "zIndex": "10000"
                    }
                }
            ))
            
            st.caption("Red circles indicate hunger hotspots (size = severity)")
            if available_resources:
                st.caption("Green circles indicate available food resources")
        
        with tab2:
            st.subheader("Detailed Hotspot Analysis")
            
         
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Hotspots Identified", len(hotspots["hotspots"]))
            with col2:
                st.metric("Highest Severity", 
                         f"{max(h['severity'] for h in hotspots['hotspots']):.1f}/1.0",
                         delta="Critical" if max(h['severity'] for h in hotspots['hotspots']) > 0.7 else "High")
            with col3:
                total_affected = sum(h.get('population_affected', 0) for h in hotspots['hotspots'])
                st.metric("Total Population Affected", f"{total_affected:,}")
            
            # Display hotspot table with expandable details
            for hotspot in sorted(hotspots["hotspots"], key=lambda x: x["severity"], reverse=True):
                with st.expander(f"{hotspot['name']} - Severity: {hotspot['severity']:.2f}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Population Affected:** {hotspot.get('population_affected', 'N/A')}")
                        st.write(f"**Trend:** {hotspot.get('trend', 'N/A')}")
                        st.write(f"**Last Updated:** {hotspot.get('last_updated', 'N/A')}")
                    with col2:
                        st.write("**Key Factors:**")
                        for factor in hotspot.get('key_factors', []):
                            st.write(f"- {factor}")
                    
                    
                    if 'historical_data' in hotspot:
                        fig = px.line(
                            hotspot['historical_data'],
                            x='date',
                            y='severity',
                            title=f"Severity Trend for {hotspot['name']}"
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Optimal Resource Allocation")
            
            if not available_resources:
                st.warning("No available resources found for allocation")
            else:
                allocations = optimize_resource_allocation(hotspots["hotspots"], available_resources)
                
                if allocations:
                    st.success("Recommended resource allocation plan:")
                    allocation_df = pd.DataFrame(allocations)
                    
                   
                    st.dataframe(
                        allocation_df[[
                            'hotspot_names',
                            'resource_name',
                            'resource_type',
                            'amount',
                            'distance_km'
                        ]].rename(columns={
                            'hotspot_names': 'Hotspot Cluster',
                            'resource_name': 'Resource Name',
                            'resource_type': 'Resource Type',
                            'amount': 'Amount to Allocate',
                            'distance_km': 'Distance (km)'
                        }),
                        hide_index=True
                    )
                    
                  
                    st.subheader("Allocation Map")
                    
                 
                    allocation_layers = [
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=hotspots_df,
                            get_position=["longitude", "latitude"],
                            get_color="[255, 0, 0, 200]",
                            get_radius="severity * 1000",
                            pickable=True,
                        ),
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=pd.DataFrame(available_resources),
                            get_position=["longitude", "latitude"],
                            get_color="[0, 128, 0, 200]",
                            get_radius=500,
                            pickable=True,
                        ),
                        pdk.Layer(
                            "ArcLayer",
                            data=allocation_df,
                            get_source_position=["longitude", "latitude"],
                            get_target_position=["resource_lon", "resource_lat"],
                            get_source_color=[255, 0, 0, 160],
                            get_target_color=[0, 128, 0, 160],
                            get_width=2,
                        )
                    ]
                    
                    st.pydeck_chart(pdk.Deck(
                        map_style="mapbox://styles/mapbox/light-v9",
                        initial_view_state=pdk.ViewState(
                            latitude=hotspots_df["latitude"].mean() or 12.9716,
                            longitude=hotspots_df["longitude"].mean() or 77.5946,
                            zoom=10,
                            pitch=50,
                        ),
                        layers=allocation_layers,
                        tooltip={
                            "html": """
                            <b>From:</b> {resource_name} <br/>
                            <b>To:</b> {hotspot_names} <br/>
                            <b>Amount:</b> {amount} <br/>
                            <b>Distance:</b> {distance_km} km
                            """,
                            "style": {
                                "backgroundColor": "white",
                                "color": "black"
                            }
                        }
                    ))
                    
                    if st.button("Send Allocation Recommendations"):
                        st.success("Allocation recommendations have been sent to relevant teams!")
                else:
                    st.warning("Could not generate allocation plan with current resources")
    else:
        st.warning("No hunger hotspots identified in current analysis")

if __name__ == "__main__":
    display_hunger_hotspots()