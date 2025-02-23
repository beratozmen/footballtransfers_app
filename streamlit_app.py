import streamlit as st
import pandas as pd
import plotly.express as px
import kagglehub
from kagglehub import KaggleDatasetAdapter

st.title("Team Total Transfer Fees Analysis")

# --------------------------------------------------------------------
# DATA LOADING: Download all datasets via KaggleHub
# --------------------------------------------------------------------
@st.cache_data
def load_all_datasets():
    # List of filenames to load from the dataset
    file_names = [
        "game_lineups.csv",
        "competitions.csv",
        "appearances.csv",
        "player_valuations.csv",
        "game_events.csv",
        "transfers.csv",
        "players.csv",
        "games.csv",
        "club_games.csv",
        "clubs.csv"
    ]
    
    data = {}
    for file in file_names:
        # Load each CSV file as a Pandas DataFrame
        data[file] = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "davidcariboo/player-scores",
            file,
            pandas_kwargs={}
        )
    return data

data = load_all_datasets()

# --------------------------------------------------------------------
# Helper function to convert season strings to full starting year
# --------------------------------------------------------------------
def season_to_year(season_str):
    """
    Converts a season string in the format "YY/YY" to a full year.
    Assumes that if the starting number is <= 50, then it is 2000+value,
    otherwise it is 1900+value.
    For example:
      "93/94" -> 1993
      "10/11" -> 2010
    """
    try:
        parts = season_str.split("/")
        start = int(parts[0])
        if start <= 50:
            full_year = 2000 + start
        else:
            full_year = 1900 + start
        return full_year
    except Exception as e:
        return 0  # fallback if conversion fails

# --------------------------------------------------------------------
# FILTERING & AGGREGATION: Total Transfer Fees with Season and Team Filters
# --------------------------------------------------------------------
# Get the transfers DataFrame from the loaded datasets
transfers_df = data["transfers.csv"].copy()

# Convert the transfer_fee column to numeric
transfers_df["transfer_fee"] = pd.to_numeric(transfers_df["transfer_fee"], errors="coerce")

# Filter out rows with missing transfer_season
transfers_df = transfers_df.dropna(subset=["transfer_season"])

# Filter out seasons before 10/11 (i.e. before 2010)
transfers_df = transfers_df[transfers_df["transfer_season"].apply(season_to_year) >= 2010]

# Create the Season filter dropdown (with "All Seasons" option)
seasons = sorted(transfers_df["transfer_season"].unique())
selected_season = st.selectbox("Select Season", ["All Seasons"] + seasons)

# Create the Team filter dropdown (with "All Teams" option)
teams = sorted(transfers_df["to_club_name"].dropna().unique())
selected_team = st.selectbox("Select Team", ["All Teams"] + teams)

# Only proceed if at least one filter is specific
if selected_season == "All Seasons" and selected_team == "All Teams":
    st.write("Please select a specific Season or a specific Team to view the data.")
else:
    df_filtered = transfers_df.copy()
    
    if selected_season != "All Seasons":
        df_filtered = df_filtered[df_filtered["transfer_season"] == selected_season]
        
    if selected_team != "All Teams":
        df_filtered = df_filtered[df_filtered["to_club_name"].str.contains(selected_team, case=False, na=False)]
    
    # Drop rows with missing transfer fees
    df_filtered = df_filtered.dropna(subset=["transfer_fee"])
    
    # Scenario 1: Specific Team and All Seasons → Group by Season for that team.
    if selected_team != "All Teams" and selected_season == "All Seasons":
        grouped = df_filtered.groupby("transfer_season")["transfer_fee"].sum().reset_index()
        x_col = "transfer_season"
        chart_title = f"Total Transfer Fees by Season for {selected_team}"
        
        fig = px.bar(
            grouped,
            x=x_col,
            y="transfer_fee",
            labels={x_col: "Season", "transfer_fee": "Total Transfer Fees (EUR)"},
            title=chart_title
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Scenario 2: Specific Season and All Teams → Group by Team for that season.
    elif selected_team == "All Teams" and selected_season != "All Seasons":
        grouped = df_filtered.groupby("to_club_name")["transfer_fee"].sum().reset_index()
        x_col = "to_club_name"
        chart_title = f"Total Transfer Fees for Teams in {selected_season}"
        
        fig = px.bar(
            grouped,
            x=x_col,
            y="transfer_fee",
            labels={x_col: "Team", "transfer_fee": "Total Transfer Fees (EUR)"},
            title=chart_title
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Scenario 3: Both specific Team and specific Season → Display total fee as text.
    else:
        total_fee = df_filtered["transfer_fee"].sum()
        st.write(f"Total Transfer Fees for {selected_team} in {selected_season}: EUR {total_fee:,.2f}")
