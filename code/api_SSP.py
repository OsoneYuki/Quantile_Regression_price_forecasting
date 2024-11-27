import requests
import pandas as pd
from datetime import datetime, timedelta

# ELEXONから提供されたURL
url = "https://downloads.elexonportal.co.uk/file/download/SSPSBPNIV_FILE?key=xovy6sugzj9gpf9"

# ファイルをダウンロードする関数
def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to download file")

# ファイル名を指定してダウンロード
download_file(url, "competition_price/data/downloaded_file")


# ファイルのパスを定義
file_path = "competition_price/data/downloaded_file"

# 日付の形式エラーを解決するために、適切な日付形式を指定して読み込む
# 元のファイルの日付形式は 'dd/mm/yyyy' と推測される

df = pd.read_csv(file_path, parse_dates=['Settlement Date'], dayfirst=True)

# Settlement Dateの形式を変更（例: '2020-09-20 00:00:00+00:00'）
df['dtm'] = df['Settlement Date'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')

# '2020-09-20 00:00:00+00:00'より前のデータを削除
cutoff_date = '2020-09-20 00:00:00+00:00'
df = df[df['dtm'] >= cutoff_date]

# Settlement Periodを30分ごとの時間に変換し、dtmと統合
df['dtm'] = df.apply(lambda x: datetime.strptime(x['dtm'], '%Y-%m-%d %H:%M:%S+00:00') + timedelta(minutes=(int(x['Settlement Period']) - 1) * 30), axis=1)

# 不要なカラム（Settlement DateとSettlement Period）を削除
df.drop(['Settlement Date', 'Settlement Period', 'System Buy Price(GBP/MWh)', 'Net Imbalance Volume(MWh)'], axis=1, inplace=True)

# カラム名を変更：System Sell Price(GBP/MWh) -> SS_Price
df.rename(columns={'System Sell Price(GBP/MWh)': 'SS_Price'}, inplace=True)

# 新しいCSVファイルとして同じディレクトリに保存
new_file_path = file_path.replace('competition_price/data/downloaded_file', 'competition_price/data/API_SS_Price.csv')
df.to_csv(new_file_path, index=False)
print("Data updated and saved to API_SS_Price.csv")