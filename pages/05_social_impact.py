import streamlit as st
from utils.database import get_db
from utils.config import get_config
from utils.notifications import get_notifications
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
import random
from PIL import Image
import base64
import io


db = get_db()
config = get_config()
notify = get_notifications()


st.set_page_config(page_title="Impact Tracker", page_icon="", layout="wide")


st.markdown("""
<style>
    /* Main card styling */
    .metric-card {
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Leaderboard styling */
    .leaderboard-row {
        transition: all 0.3s ease;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
    }
    
    .leaderboard-row:hover {
        background-color: #f0f2f6;
        transform: translateY(-2px);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    /* Progress bar styling */
    .progress-container {
        height: 8px;
        border-radius: 4px;
        background-color: #e0e0e0;
        margin-top: 8px;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Champion crown icon */
    .crown-icon {
        color: gold;
        font-size: 18px;
        margin-left: 4px;
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_user_impact(user_id):
    """Generate realistic mock impact data for a user"""
    return {
        "user_id": user_id,
        "score": random.randint(50, 200),
        "meals_provided": random.randint(10, 100),
        "co2_saved": round(random.uniform(5, 50), 1),
        "waste_reduced": round(random.uniform(2, 30), 1),
        "last_updated": datetime.now(),
        "badges": random.sample(
            ["Meal Hero", "Eco Warrior", "Waste Buster", "Local Champion", "Sustainability Star"],
            k=random.randint(1, 3))
    }

def generate_mock_leaderboard(num_users=10):
    """Generate a mock leaderboard with realistic data"""
    locations = ["Pune", "Kolkata", "New Delhi", "Mumbai", "Bangalore", "Hyderabad"]
    users = []
    
    for i in range(num_users):
        score = random.randint(50, 250)
        users.append({
            "username": f"User_{i+1}",
            "impact_score": score,
            "location": random.choice(locations),
            "is_champion": score >= 100,
            "avatar": f"https://i.pravatar.cc/150?img={i+1}"
        })
    
   
    if 'user_id' in st.session_state:
        current_user = {
            "username": "You",
            "impact_score": random.randint(100, 200),
            "location": "Current Location",
            "is_champion": True,
            "avatar": "https://i.pravatar.cc/150?img=50"
        }
        users.append(current_user)
    
    return sorted(users, key=lambda x: x['impact_score'], reverse=True)

def generate_mock_activity(user_id, days=30):
    """Generate mock activity data for a user"""
    activities = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        activities.append({
            "date": date.strftime("%Y-%m-%d"),
            "meals_provided": random.randint(0, 5),
            "co2_saved": round(random.uniform(0, 2.5), 1),
            "waste_reduced": round(random.uniform(0, 1.5), 1),
            "score": random.randint(0, 10)
        })
    return activities


def get_real_user_impact(user_id):
    """Get real impact data from database"""
    impact = db.get_collection(config.collections["social_impact"]).find_one(
        {"user_id": user_id})
    
    if not impact:
        return generate_mock_user_impact(user_id)
    
    
    impact.setdefault("meals_provided", 0)
    impact.setdefault("co2_saved", 0)
    impact.setdefault("waste_reduced", 0)
    impact.setdefault("score", 0)
    impact.setdefault("badges", [])
    
    return impact

def get_real_leaderboard():
    """Get real leaderboard data from database"""
    try:
        users = list(db.get_collection(config.collections["users"]).find({}, {
            "username": 1,
            "location": 1,
            "avatar": 1
        }))
        
        leaderboard = []
        for user in users:
            impact = db.get_collection(config.collections["social_impact"]).find_one(
                {"user_id": user["_id"]})
            
            if impact:
                leaderboard.append({
                    "username": user.get("username", "Unknown"),
                    "impact_score": impact.get("score", 0),
                    "location": user.get("location", "Unknown"),
                    "is_champion": impact.get("score", 0) >= 100,
                    "avatar": user.get("avatar", "https://i.pravatar.cc/150")
                })
        
        if not leaderboard:
            return generate_mock_leaderboard()
        
        return sorted(leaderboard, key=lambda x: x['impact_score'], reverse=True)
    except:
        return generate_mock_leaderboard()

def get_real_user_activity(user_id):
    """Get real activity data from database"""
    try:
        activities = list(db.get_collection(config.collections["user_activity"]).find(
            {"user_id": user_id},
            {"date": 1, "meals_provided": 1, "co2_saved": 1, "waste_reduced": 1, "score": 1}
        ).sort("date", 1))
        
        if not activities:
            return generate_mock_activity(user_id)
        
       
        formatted_activities = []
        for act in activities:
            formatted_activities.append({
                "date": act.get("date", datetime.now()).strftime("%Y-%m-%d"),
                "meals_provided": act.get("meals_provided", 0),
                "co2_saved": act.get("co2_saved", 0),
                "waste_reduced": act.get("waste_reduced", 0),
                "score": act.get("score", 0)
            })
        
        return formatted_activities
    except:
        return generate_mock_activity(user_id)


def display_impact_metrics(impact_data):
    """Display the main impact metrics cards"""
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Impact Score</h3>
            <h1>{impact_data['score']}</h1>
            <div class="progress-container">
                <div class="progress-bar" style="width: {min(impact_data['score']/250*100, 100)}%"></div>
            </div>
            <p>Progress to next level: {int(min(impact_data['score']/250*100, 100))}% (250 pts)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Meals Provided</h3>
            <h1>{impact_data['meals_provided']}</h1>
            <p>{int(impact_data['meals_provided']/50*100)}% to next badge</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <h3>CO₂ Saved</h3>
            <h1>{impact_data['co2_saved']} kg</h1>
            <p>{int(impact_data['co2_saved']/20*100)}% to next badge</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Waste Reduced</h3>
            <h1>{impact_data['waste_reduced']} kg</h1>
            <p>{int(impact_data['waste_reduced']/15*100)}% to next badge</p>
        </div>
        """, unsafe_allow_html=True)

def display_badges(badges):
    """Display earned badges"""
    st.subheader("Your Achievements")
    if badges:
        cols = st.columns(4)
        for i, badge in enumerate(badges):
            with cols[i % 4]:
                st.markdown(f"""
                <div style="text-align: center; padding: 12px; border-radius: 8px; background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);">
                    <div style="font-size: 32px;">{"🏆" if "Champion" in badge else "🌟"}</div>
                    <h4>{badge}</h4>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Complete more actions to earn badges!")

def display_activity_chart(activities):
    """Display the activity timeline chart"""
    if not activities:
        st.info("No activity data available yet")
        return
    
    df = pd.DataFrame(activities)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = px.line(df, x='date', y=['meals_provided', 'co2_saved', 'waste_reduced'],
                 title="Your Activity Timeline",
                 labels={"date": "Date", "value": "Amount", "variable": "Metric"},
                 line_shape="spline",
                 color_discrete_sequence=['#4CAF50', '#2196F3', '#FF9800'])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_leaderboard(leaderboard_data, current_user_id):
    """Display the interactive leaderboard"""
    st.subheader(" Community Leaderboard")
    

    current_user_pos = None
    for i, user in enumerate(leaderboard_data):
        if user.get("username") == "You" or user.get("user_id") == current_user_id:
            current_user_pos = i + 1
            break
    
 
    cols = st.columns(3)
    podium_colors = ['#FFD700', '#C0C0C0', '#CD7F32']
    
    for i in range(min(3, len(leaderboard_data))):
        with cols[i]:
            user = leaderboard_data[i]
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; border-radius: 12px; 
                        background: linear-gradient(135deg, {podium_colors[i]} 0%, #f5f7fa 100%);">
                <h3>#{i+1}</h3>
                <img src="{user['avatar']}" width="80" style="border-radius: 50%; border: 3px solid white;">
                <h4>{user['username']}</h4>
                <h2>{user['impact_score']} pts</h2>
                <p>{user['location']}</p>
                {"👑" if user['is_champion'] else ""}
            </div>
            """, unsafe_allow_html=True)
    

    st.markdown("### All Participants")
    
    leaderboard_df = pd.DataFrame(leaderboard_data)
    if 'user_id' in leaderboard_df.columns:
        leaderboard_df = leaderboard_df.drop(columns=['user_id'])
    

    def highlight_current_user(row):
        if row['username'] == "You" or row.get('user_id') == current_user_id:
            return ['background-color: #E3F2FD'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        leaderboard_df.style.apply(highlight_current_user, axis=1),
        column_config={
            "username": "User",
            "impact_score": st.column_config.NumberColumn(
                "Impact Score",
                format="%d pts"
            ),
            "location": "Location",
            "is_champion": st.column_config.CheckboxColumn("Champion")
        },
        use_container_width=True,
        hide_index=True
    )
    
  
    if current_user_pos:
        st.markdown(f"""
        <div style="text-align: center; padding: 12px; border-radius: 8px; background-color: #E3F2FD;">
            <h4>Your Position: #{current_user_pos} out of {len(leaderboard_data)}</h4>
            {f"<p>You're {leaderboard_data[current_user_pos-1]['impact_score'] - leaderboard_data[2]['impact_score']} pts from the podium!</p>" if current_user_pos > 3 else ""}
        </div>
        """, unsafe_allow_html=True)

def display_community_stats(leaderboard_data):
    """Display community statistics"""
    st.subheader("Community Statistics")
    
    if not leaderboard_data:
        st.info("No community data available yet")
        return
    
    df = pd.DataFrame(leaderboard_data)
    
    cols = st.columns(3)
    with cols[0]:
        avg_score = df['impact_score'].mean()
        st.metric("Average Score", f"{avg_score:.0f} pts", 
                 delta=f"{avg_score-100:.0f} vs goal")
    
    with cols[1]:
        median_score = df['impact_score'].median()
        st.metric("Median Score", f"{median_score:.0f} pts")
    
    with cols[2]:
        max_score = df['impact_score'].max()
        st.metric("Highest Score", f"{max_score:.0f} pts")
    
   
    st.subheader("Score Distribution")
    fig = px.histogram(df, x='impact_score', nbins=20,
                      title="Community Impact Score Distribution",
                      labels={'impact_score': 'Impact Score'},
                      color_discrete_sequence=['#4CAF50'])
    
    fig.update_layout(
        bargap=0.1,
        xaxis_title="Impact Score",
        yaxis_title="Number of Users",
        showlegend=False
    )
    
 
    fig.add_vline(x=100, line_dash="dash", line_color="red", 
                 annotation_text="Champion Threshold", 
                 annotation_position="top right")
    
    st.plotly_chart(fig, use_container_width=True)


def impact_tracker_page():
    """Main impact tracker page"""
    st.title("Your Impact Tracker")
    st.markdown("Track your contributions to food sustainability and see how you compare to others in the community.")
    
 
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to access impact tracking features")
        return
    
   
    try:
        user_impact = get_real_user_impact(st.session_state.user_id)
        leaderboard_data = get_real_leaderboard()
        user_activity = get_real_user_activity(st.session_state.user_id)
        using_mock_data = False
    except Exception as e:
        st.warning("Using mock data while connecting to database...")
        user_impact = generate_mock_user_impact(st.session_state.user_id)
        leaderboard_data = generate_mock_leaderboard()
        user_activity = generate_mock_activity(st.session_state.user_id)
        using_mock_data = True
    
 
    display_impact_metrics(user_impact)
    display_badges(user_impact.get('badges', []))
    
    
    st.subheader(" Your Activity Timeline")
    display_activity_chart(user_activity)
    
 
    st.subheader(" Community Impact")
    tab1, tab2 = st.tabs(["Leaderboard", "Statistics"])
    
    with tab1:
        display_leaderboard(leaderboard_data, st.session_state.user_id)
    
    with tab2:
        display_community_stats(leaderboard_data)
    
 
    st.subheader(" Share Your Impact")
    
    share_cols = st.columns([3, 1])
    with share_cols[0]:
        share_message = st.text_area(
            "Customize your share message",
            value=f""" My FoodConnect Impact 

I've contributed to:
- {user_impact['meals_provided']} meals provided 
- {user_impact['co2_saved']} kg CO₂ saved 
- {user_impact['waste_reduced']} kg waste reduced 

My current impact score: {user_impact['score']} pts
Current rank: #{next((i+1 for i, u in enumerate(leaderboard_data) if u.get('username') == 'You' or u.get('user_id') == st.session_state.user_id), 1)} in the community

Join me in making a difference with FoodConnect!""",
            height=150
        )
    
    with share_cols[1]:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("Share via WhatsApp", help="Share your impact with friends"):
            if notify:
                if notify.send_whatsapp_message(
                    user_impact.get('phone', ''),  
                    share_message
                ):
                    st.success("Impact summary shared via WhatsApp!")
                else:
                    st.error("Failed to send WhatsApp message")
            else:
                st.warning("WhatsApp notifications not configured")
    
    
    if not using_mock_data:
        st.markdown("""
        <script>
        // Auto-refresh every 30 seconds for real-time updates
        setTimeout(function(){
            window.location.reload();
        }, 30000);
        </script>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    impact_tracker_page()