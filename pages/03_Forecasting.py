import pandas as pd
import streamlit as st
from datetime import timedelta
import plotly.express as px

from models.predictor import (spending_predictor,get_daily_spending_history,create_feature)

st.set_page_config(page_title='Spending Forecast',page_icon="🔮",layout="wide")
st.title('Spending Forecast 🔮')

if "user_id" not in st.session_state:
    st.warning("Please log in by entering a username on the Home page first.")
    st.stop()

user_id = st.session_state['user_id']
predictor = spending_predictor(user_id)

if not predictor.model_path.exists():
    st.info("You haven't trained a prediction model yet. Please train one to see your forecast.")
    if st.button('Train Prediction Model',type="primary"):
        with st.spinner("Training model... This may take a moment."):
            historical_data = get_daily_spending_history(user_id)
            if len(historical_data)<14:
                st.error("Not enough historical data to train a model. Please use a statement with at least 14 days of spending.")
            else:
                featured_data = create_feature(historical_data)
                feature = ['dayofweek','dayofmonth','month','year','lag_7','rolling_7_day_avg']
                target = ['total_spending']
                X= featured_data[feature]
                y= featured_data[target]
                predictor.train(X,y)
                st.success("Model Trained Successfully!")
                st.rerun()

else:
    st.header("Your Projected Spending")
    forecasting_days = st.slider('Select how many days to forecast:',30,180,90)
    if st.button("",type="primary"):
        st.spinner("")
        predictor.load_model()
        historical_data = get_daily_spending_history(user_id)
        last_known_day = historical_data.index.max()
        future_dates = pd.date_range(start=last_known_day + timedelta(days=1),periods=forecasting_days)
        forecasted_df = pd.DataFrame(index=future_dates,columns=["total_spending"])
        temp_df = historical_data.copy()

        for date in future_dates:
            full_featured_df = create_feature(temp_df.tail(30))
            x_to_predict = full_featured_df.tail(1)[['dayofweek','dayofmonth','month','year','lag_7','rolling_7_day_avg']]
            prediction = predictor.predict(x_to_predict)[0]

            forecasted_df.loc[date,'total_spending'] = prediction
            new_row = pd.DataFrame({'total_spending':[prediction]},index=[date])
            temp_df = pd.concat([temp_df,new_row])

        historical_data['type'] = 'Historical'
        forecasted_df['type'] = 'Forecast'
        plot_df = pd.concat([historical_data, forecasted_df])
        plot_df.reset_index(inplace=True)
        plot_df.rename(columns={'index': 'date'}, inplace=True)

            # Create the chart
        fig = px.line(
            plot_df,
            x='date',
            y='total_spending',
            color='type',
            title="Historical vs. Forecasted Daily Spending",
            labels={'total_spending': 'Spending (₹)', 'date': 'Date'}
        )
        fig.update_traces(selector=dict(name="Forecast"), line=dict(dash='dot'))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Retrain Model with Latest Data"):
        # This logic is the same as the initial training button
        st.session_state['force_retrain'] = True  # Use session state to confirm

    if 'force_retrain' in st.session_state and st.session_state['force_retrain']:
        if st.checkbox("I understand this will replace the existing model. Proceed."):
            with st.spinner("Retraining model..."):
                historical_data = get_daily_spending_history(user_id)
                featured_data = create_feature(historical_data)
                FEATURES = ['dayofweek', 'dayofmonth', 'month', 'year', 'lag_7', 'rolling_7_day_avg']
                TARGET = 'total_spending'
                X = featured_data[FEATURES]
                y = featured_data[TARGET]
                predictor.train(X, y)
                st.success("Model retrained successfully!")
                del st.session_state['force_retrain']
                st.rerun()






