import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

@st.cache_data(show_spinner=False)
def transfer_history(player_url):
    # Extract the player ID from the URL.
    try:
        playerid = player_url.split("spieler/")[1]
    except IndexError:
        st.error("The URL does not seem to be a valid Transfermarkt player URL.")
        return pd.DataFrame()
    
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/90.0.4430.212 Safari/537.36'
        )
    }
    
    try:
        r = requests.get(player_url, headers=headers, timeout=1000)
    except Exception as e:
        st.error(f"Error fetching the URL: {e}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Get the player's name from the header.
    try:
        name = soup.find("h1").get_text().strip()
    except Exception as e:
        st.error("Could not extract the player's name.")
        return pd.DataFrame()
    
    # Try to locate the transfer history table by scanning all divs with class "responsive-table".
    table_divs = soup.find_all("div", class_="responsive-table")
    transfer_table = None
    for div in table_divs:
        table = div.find("table")
        if table and ("Sezon" in table.get_text() or "Season" in table.get_text()):
            transfer_table = table
            break
    
    if transfer_table is None:
        st.error("Could not find the transfer history table. The page structure may have changed.")
        return pd.DataFrame()
    
    try:
        df_list = pd.read_html(str(transfer_table))
        if not df_list:
            st.error("No table data found on the page.")
            return pd.DataFrame()
        temp = df_list[0]
    except Exception as e:
        st.error(f"Error reading the table: {e}")
        return pd.DataFrame()
    
    # Clean the data by removing summary rows and unnecessary columns.
    try:
        temp = temp[temp.Sezon != "Toplam transfer kazancı :"]
    except Exception:
        pass  # If the column isn't present, continue.
    
    drop_cols = ["Unnamed: 10", "Veren kulüp", "Veren kulüp.1", "Alan kulüp", "Alan kulüp.1"]
    for col in drop_cols:
        if col in temp.columns:
            temp = temp.drop(col, axis=1)
    temp = temp.rename(columns={"Veren kulüp.2": "VerenKulup", "Alan kulüp.2": "AlanKulup"})
    temp["TMId"] = playerid
    temp["Player"] = name
    return temp

def main():
    st.title("Transfermarkt: Player Transfer History")
    st.markdown("""
    This demo shows how to scrape a player's transfer history from Transfermarkt.
    
    **Note:** The full team-level analysis would involve scraping:
    - League URLs for your season(s) of interest
    - Team URLs from those leagues
    - Player URLs from a chosen team
    - Then aggregating the transfer history of each player
    
    The code below focuses on a single player (using Mesut Özil’s profile as an example) for clarity.
    """)
    
    default_url = "https://www.transfermarkt.com.tr/mesut-ozil/profil/spieler/35664"
    player_url = st.text_input("Enter a Transfermarkt player URL:", default_url)
    
    if st.button("Get Transfer History"):
        with st.spinner("Fetching transfer history data..."):
            df_transfer = transfer_history(player_url)
        if not df_transfer.empty:
            st.success("Transfer history data fetched successfully!")
            st.dataframe(df_transfer)
        else:
            st.error("No transfer history data could be retrieved. Check the URL or try again.")

if __name__ == "__main__":
    main()
