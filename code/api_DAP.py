import requests
from requests import Session
import requests
import pandas as pd
import datetime
import warnings
from datetime import datetime, timedelta


class RebaseAPI:
  
  challenge_id = 'heftcom2024'
  base_url = 'https://api.rebase.energy'

  def __init__(
    self,
    api_key = open("competition_price/data/team_key.txt").read()
    ):
    self.api_key = api_key
    self.headers = {
      'Authorization': f"Bearer {api_key}"
      }
    self.session = Session()
    self.session.headers = self.headers


  def get_variable(
      self,
      day: str,
      variable: ["market_index",
                 "day_ahead_price",
                 "imbalance_price",
                 "wind_total_production",
                 "solar_total_production",
                 "solar_and_wind_forecast"
                 ],
                 ):
    url = f"{self.base_url}/challenges/data/{variable}"
    params = {'day': day}
    resp = self.session.get(url, params=params)

    data = resp.json()
    df = pd.DataFrame(data)
    return df
def fetch_data(start_date, end_date, variable):
    api = RebaseAPI()
    all_data = pd.DataFrame()
    current_date = start_date

    while current_date <= end_date:
        df = api.get_variable(current_date.strftime('%Y-%m-%d'), variable)
        all_data = pd.concat([all_data, df])
        current_date += timedelta(days=1)

    return all_data

# 既存のCSVファイルを読み込む
existing_df = pd.read_csv('competition_price/data/API_DA_Price.csv')
existing_df['timestamp_utc'] = pd.to_datetime(existing_df['timestamp_utc']).dt.date

# 最後の日付を取得
last_date = existing_df['timestamp_utc'].max()

# 現在の日付を取得 (タイムゾーン情報なし)
current_date = datetime.now().date()

# 最後の日付が現在の日付より前の場合、不足しているデータを取得
if last_date < current_date:
    # 最後の日付の翌日からデータを取得
    start_date = last_date + timedelta(days=1)
    end_date = current_date
    variable = 'day_ahead_price'
      
    # 新たなデータを取得
    new_data = fetch_data(start_date, end_date, variable)
    new_file_name = 'competition_price/data/New_API_DA_Price.csv'
    new_data.to_csv(new_file_name, index=False)

    # 新旧データを結合
    updated_df = pd.concat([existing_df, new_data]).drop_duplicates().reset_index(drop=True)

    # CSVファイルに保存
    updated_df.to_csv('competition_price/data/API_DA_Price.csv', index=False)
    print("Data updated and saved to API_DA_Price.csv")
else:
    print("No new data to update.")








