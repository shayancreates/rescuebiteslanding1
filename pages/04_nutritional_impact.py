import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.config import get_config
from utils.langgraph_flows import get_langgraph_flows
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random


db = get_db()
ai = get_ai_agents()
config = get_config()
flows = get_langgraph_flows()



st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .summary-card {
        background-color: #e9f7ef;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border-left: 5px solid #2ecc71;
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stSelectbox div[data-baseweb="select"] {
        margin-bottom: 10px;
    }
    .data-source-tag {
        font-size: 0.8em;
        color: #666;
        font-style: italic;
        margin-top: 5px;
    }
    .mock-data-warning {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


st.title("Nutritional Impact Dashboard")
st.markdown("""
### Visualize and understand the nutritional value of your meals
""")


if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.warning("Please login to access nutritional impact features")
    st.stop()


user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
if not user:
    st.error("User not found")
    st.stop()


def generate_mock_nutrition_data(days=7):
    base_date = datetime.now() - timedelta(days=days)
    data = []
    
    for i in range(days):
        day_date = base_date + timedelta(days=i)
        day_name = day_date.strftime("%A")
        
      
        calories = random.randint(1800, 2500)
        protein = random.randint(60, 120)
        carbs = random.randint(200, 350)
        fat = random.randint(50, 100)
        fiber = random.randint(20, 35)
        sugar = random.randint(30, 70)
        
        data.append({
            "day": day_name,
            "date": day_date.strftime("%Y-%m-%d"),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "fiber": fiber,
            "sugar": sugar,
            "is_mock": True  
        })
    
    return pd.DataFrame(data)


def get_real_nutrition_data():
    if "current_meal_plan" in st.session_state:
        plan = st.session_state.current_meal_plan
    else:
        latest_plan = db.get_collection(config.collections["meal_plans"]).find_one(
            {"user_id": st.session_state.user_id},
            sort=[("created_at", -1)]
        )
        if latest_plan:
            st.session_state.current_meal_plan = latest_plan["plan"]
            plan = latest_plan["plan"]
        else:
            plan = None
    
    if not plan:
        return None
    
    if isinstance(plan, str):
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError:
            return None
    
    nutrition_data = []
    
    if "days" not in plan:
        return None
    
    for day, meals in plan["days"].items():
        if "nutritional_info" in meals:
            nutrients = meals["nutritional_info"]
            if isinstance(nutrients, dict):
                nutrients["day"] = day
                nutrients["is_mock"] = False  
                nutrition_data.append(nutrients)
    
    if not nutrition_data:
        return None
    
    return pd.DataFrame(nutrition_data)


def combine_data(real_data, mock_data):
    if real_data is None:
        return mock_data, "Mock Data (Sample)"
    

    common_cols = list(set(real_data.columns) & set(mock_data.columns))
    real_data = real_data[common_cols]
    mock_data = mock_data[common_cols]
    

    combined = pd.concat([real_data, mock_data]).sort_values("day")
    return combined, "Combined Real and Sample Data"


nutrition_df = get_real_nutrition_data()
mock_df = generate_mock_nutrition_data()

if nutrition_df is not None and not nutrition_df.empty:
    nutrition_df, data_source = combine_data(nutrition_df, mock_df)
    st.session_state.data_source = data_source
else:
    nutrition_df = mock_df
    st.session_state.data_source = "Mock Data (Sample)"
    st.markdown("""
    <div class="mock-data-warning">
        ℹ️ You haven't generated any meal plans yet. We're showing sample data to help you explore the dashboard. 
        Visit the Personalized Nutrition page to create your first meal plan!
    </div>
    """, unsafe_allow_html=True)


st.markdown(f"<div class='data-source-tag'>Displaying: {st.session_state.data_source}</div>", 
            unsafe_allow_html=True)


def calculate_daily_requirements(user):
    
    age = user.get("age", 30)
    gender = user.get("gender", "Male").lower()
    activity_level = user.get("activity_level", "Moderately Active").lower()
    
    if gender == "male":
        bmr = 88.362 + (13.397 * 70) + (4.799 * 175) - (5.677 * age)  # Using average weight/height for demo
    else:
        bmr = 447.593 + (9.247 * 60) + (3.098 * 162) - (4.330 * age)  # Using average weight/height for demo
    
  
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extremely active": 1.9
    }
    
    calories = bmr * activity_multipliers.get(activity_level, 1.55)
    
    
    protein = calories * 0.3 / 4  # 30% of calories, 4 cal/g
    carbs = calories * 0.5 / 4    # 50% of calories, 4 cal/g
    fat = calories * 0.2 / 9      # 20% of calories, 9 cal/g
    
    return {
        "calories": round(calories),
        "protein": round(protein),
        "carbs": round(carbs),
        "fat": round(fat),
        "fiber": 30, 
        "sugar": 50    
    }

daily_reqs = calculate_daily_requirements(user)


st.subheader("Your Nutritional Summary")


def generate_summary_insights(nutrition_df, daily_reqs):
    real_data = nutrition_df[nutrition_df['is_mock'] == False] if 'is_mock' in nutrition_df.columns else nutrition_df
    avg_calories = real_data['calories'].mean() if not real_data.empty else nutrition_df['calories'].mean()
    calorie_percentage = (avg_calories / daily_reqs['calories']) * 100
    
    avg_protein = real_data['protein'].mean() if not real_data.empty else nutrition_df['protein'].mean()
    protein_percentage = (avg_protein / daily_reqs['protein']) * 100
    
    highest_day = nutrition_df.loc[nutrition_df['calories'].idxmax()]
    lowest_day = nutrition_df.loc[nutrition_df['calories'].idxmin()]
    
    insights = []
    
    if not real_data.empty:
        insights.append("📊 Showing your actual meal plan data")
    else:
        insights.append("ℹ️ Currently showing sample data - generate a meal plan to see your personal insights")
    
    if calorie_percentage > 90:
        insights.append(f"Your meals provide {calorie_percentage:.0f}% of your daily calorie needs - great balance!")
    elif calorie_percentage > 70:
        insights.append(f"Your meals provide {calorie_percentage:.0f}% of your daily calorie needs - almost there!")
    else:
        insights.append(f"Your meals provide {calorie_percentage:.0f}% of your daily calorie needs - consider adding more nutrient-dense foods.")
    
    if protein_percentage > 100:
        insights.append(f"Excellent protein intake at {protein_percentage:.0f}% of your daily requirement!")
    elif protein_percentage > 80:
        insights.append(f"Good protein intake at {protein_percentage:.0f}% of your daily requirement.")
    
    insights.append(f"Highest calorie day: {highest_day['day']} ({highest_day['calories']} kcal)")
    insights.append(f"Lowest calorie day: {lowest_day['day']} ({lowest_day['calories']} kcal)")
    
    return insights

insights = generate_summary_insights(nutrition_df, daily_reqs)

with st.container():
    st.markdown("<div class='summary-card'>", unsafe_allow_html=True)
    st.markdown("#### 🎯 Daily Nutrition Insights")
    for insight in insights:
        st.write(f"- {insight}")
    st.markdown("</div>", unsafe_allow_html=True)


col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    avg_cal = nutrition_df['calories'].mean()
    st.metric("Average Calories", f"{avg_cal:.0f} kcal", 
              f"{((avg_cal - daily_reqs['calories'])/daily_reqs['calories']*100):.1f}% of daily need")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    avg_protein = nutrition_df['protein'].mean()
    st.metric("Average Protein", f"{avg_protein:.1f} g", 
              f"{(avg_protein/daily_reqs['protein']*100):.1f}% of daily need")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    avg_carbs = nutrition_df['carbs'].mean()
    st.metric("Average Carbs", f"{avg_carbs:.1f} g", 
              f"{(avg_carbs/daily_reqs['carbs']*100):.1f}% of daily need")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    avg_fat = nutrition_df['fat'].mean()
    st.metric("Average Fat", f"{avg_fat:.1f} g", 
              f"{(avg_fat/daily_reqs['fat']*100):.1f}% of daily need")
    st.markdown("</div>", unsafe_allow_html=True)


st.subheader("Nutritional Breakdown")


chart_col1, chart_col2 = st.columns([1, 3])
with chart_col1:
    chart_type = st.selectbox("Select Chart Type", 
                            ["Bar", "Pie", "Line", "Radar"],
                            index=0,
                            key="chart_type_select")


with st.container():
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    
    
    if 'is_mock' in nutrition_df.columns:
        color_discrete_map = {
            'protein': '#3498db',
            'carbs': '#2ecc71',
            'fat': '#e74c3c',
            'Real Data': '#3498db',
            'Mock Data': '#95a5a6'
        }
    else:
        color_discrete_map = {
            'protein': '#3498db',
            'carbs': '#2ecc71',
            'fat': '#e74c3c'
        }
    
    if chart_type == "Bar":
       
        melted_df = nutrition_df.melt(id_vars=['day', 'is_mock'] if 'is_mock' in nutrition_df.columns else ['day'], 
                                    value_vars=['protein', 'carbs', 'fat'],
                                    var_name='Nutrient', 
                                    value_name='Amount (g)')
        
        if 'is_mock' in melted_df.columns:
            melted_df['Data Type'] = melted_df['is_mock'].apply(lambda x: 'Mock Data' if x else 'Real Data')
            fig = px.bar(melted_df, 
                        x='day', 
                        y='Amount (g)', 
                        color='Data Type',
                        barmode='group',
                        title="Macronutrient Distribution by Day",
                        labels={'day': 'Day', 'Amount (g)': 'Amount (grams)'},
                        color_discrete_map=color_discrete_map,
                        facet_col='Nutrient')
        else:
            fig = px.bar(melted_df, 
                        x='day', 
                        y='Amount (g)', 
                        color='Nutrient',
                        barmode='group',
                        title="Macronutrient Distribution by Day",
                        labels={'day': 'Day', 'Amount (g)': 'Amount (grams)'},
                        color_discrete_map=color_discrete_map)
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Pie":
        
        if 'is_mock' in nutrition_df.columns and len(nutrition_df['is_mock'].unique()) > 1:
            tab1, tab2 = st.tabs(["Real Data", "Mock Data"])
            
            with tab1:
                real_avg = nutrition_df[nutrition_df['is_mock'] == False][['protein', 'carbs', 'fat']].mean()
                fig = px.pie(real_avg,
                            values=real_avg.values,
                            names=real_avg.index,
                            title="Average Macronutrient Distribution (Your Data)",
                            color=real_avg.index,
                            color_discrete_map=color_discrete_map)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                mock_avg = nutrition_df[nutrition_df['is_mock'] == True][['protein', 'carbs', 'fat']].mean()
                fig = px.pie(mock_avg,
                            values=mock_avg.values,
                            names=mock_avg.index,
                            title="Average Macronutrient Distribution (Sample Data)",
                            color=mock_avg.index,
                            color_discrete_map=color_discrete_map)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        else:
            avg_nutrients = nutrition_df[['protein', 'carbs', 'fat']].mean()
            fig = px.pie(avg_nutrients,
                        values=avg_nutrients.values,
                        names=avg_nutrients.index,
                        title="Average Macronutrient Distribution",
                        color=avg_nutrients.index,
                        color_discrete_map=color_discrete_map)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
    elif chart_type == "Line":
        
        if 'is_mock' in nutrition_df.columns:
            fig = px.line(nutrition_df,
                          x='day',
                          y=['protein', 'carbs', 'fat'],
                          title="Macronutrient Trends Over Days",
                          labels={'value': 'Amount (grams)', 'day': 'Day', 'variable': 'Nutrient'},
                          color_discrete_map=color_discrete_map,
                          line_dash='is_mock',
                          line_dash_map={True: 'dot', False: 'solid'})
        else:
            fig = px.line(nutrition_df,
                          x='day',
                          y=['protein', 'carbs', 'fat'],
                          title="Macronutrient Trends Over Days",
                          labels={'value': 'Amount (grams)', 'day': 'Day', 'variable': 'Nutrient'},
                          color_discrete_map=color_discrete_map)
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
    elif chart_type == "Radar":
       
        avg_nutrients = nutrition_df[['protein', 'carbs', 'fat']].mean().to_dict()
        radar_df = pd.DataFrame({
            'Nutrient': ['Protein', 'Carbs', 'Fat'],
            'Your Intake': [avg_nutrients['protein'], avg_nutrients['carbs'], avg_nutrients['fat']],
            'Daily Requirement': [daily_reqs['protein'], daily_reqs['carbs'], daily_reqs['fat']]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=radar_df['Your Intake'],
            theta=radar_df['Nutrient'],
            fill='toself',
            name='Your Intake',
            line_color='#3498db'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=radar_df['Daily Requirement'],
            theta=radar_df['Nutrient'],
            fill='toself',
            name='Daily Requirement',
            line_color='#e74c3c'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(daily_reqs['protein'], daily_reqs['carbs'], daily_reqs['fat']) * 1.2]
                )),
            showlegend=True,
            title="Nutrient Intake vs. Daily Requirements"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


st.subheader("Additional Insights")


with st.expander("Nutrient Density Analysis"):
    st.markdown("""
    Nutrient density refers to the amount of nutrients per calorie in a food.
    Higher nutrient density means you get more vitamins, minerals, and other beneficial compounds per calorie consumed.
    """)
    
  
    nutrition_df['nutrient_density'] = (
        (nutrition_df['protein'] * 2) + 
        nutrition_df['fiber'] - 
        (nutrition_df['sugar'] * 0.5) +
        (nutrition_df['fat'] * 0.5))
    
    fig = px.bar(nutrition_df,
                 x='day',
                 y='nutrient_density',
                 title="Nutrient Density by Day",
                 labels={'day': 'Day', 'nutrient_density': 'Nutrient Density Score'},
                 color='nutrient_density',
                 color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)


with st.expander("Meal Timing Analysis"):
    st.markdown("""
    The distribution of nutrients throughout the day can impact energy levels and metabolism.
    """)
    
   
    timing_data = {
        'Meal': ['Breakfast', 'Lunch', 'Dinner', 'Snacks'],
        'Calories': [0.3 * daily_reqs['calories'], 
                    0.4 * daily_reqs['calories'], 
                    0.25 * daily_reqs['calories'], 
                    0.05 * daily_reqs['calories']]
    }
    
    fig = px.pie(timing_data,
                 values='Calories',
                 names='Meal',
                 title="Calorie Distribution Across Meals",
                 color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig, use_container_width=True)


with st.expander("Personalized Recommendations"):
    st.markdown("""
    Based on your nutritional intake and profile, here are some personalized suggestions:
    """)
    
    avg_calories = nutrition_df['calories'].mean()
    calorie_diff = avg_calories - daily_reqs['calories']
    
    if calorie_diff > 300:
        st.write("- Consider slightly reducing portion sizes to better match your calorie needs")
    elif calorie_diff < -300:
        st.write("- You might benefit from adding some nutrient-dense snacks between meals")
    
    avg_protein = nutrition_df['protein'].mean()
    protein_diff = avg_protein - daily_reqs['protein']
    
    if protein_diff < -10:
        st.write("- Try incorporating more protein-rich foods like lean meats, beans, or dairy")
    
    avg_fiber = nutrition_df['fiber'].mean()
    if avg_fiber < 25:
        st.write("- Increasing your fiber intake with whole grains and vegetables could improve digestion")


st.markdown("""
<style>
@media (max-width: 600px) {
    .metric-card {
        padding: 10px;
        margin-bottom: 10px;
    }
    .summary-card {
        padding: 10px;
    }
}
</style>
""", unsafe_allow_html=True)