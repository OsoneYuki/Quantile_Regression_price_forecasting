# 必要なライブラリをインポート
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from datetime import timedelta
from datetime import datetime
# api_DAP.py,api_SSP.pyをインポート
# これでpredict_price.py実行時に自動的にapi_DAP.py,api_SSP.pyからAPI経由でファイルを取得できる
import api_DAP
import api_SSP

#API経由で取得したファイルの結合
# 開始日時と終了日時を設定
start_date = datetime(2020, 9, 20).strftime('%Y-%m-%d')
# 現在の日付を取得し、1日加算してyyyy-MM-dd形式に変換
end_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
# 30分ごとのデータフレームを生成（ここにAPI経由で取得したファイルデータを結合していく）
date_range = pd.date_range(start_date, end_date, freq='30min')
df_date_only = pd.DataFrame(date_range, columns=['dtm'])
# 同じディレクトリにあるファイルを呼び出す
df1 = pd.read_csv('competition_price/data/API_DA_Price.csv')
df2 = pd.read_csv('competition_price/data/API_SS_Price.csv')
# df2のdtmカラムをdatetime型に変換
df1['dtm'] = pd.to_datetime(df1['dtm'])
df2['dtm'] = pd.to_datetime(df2['dtm'])
# df1のdtmカラムのタイムゾーン情報を削除し、datetime64[ns]型に変換
df1['dtm'] = pd.to_datetime(df1['dtm']).dt.tz_localize(None)
# df1のpriceカラムの名前をDA_Priceに変更
df1.rename(columns={'price': 'DA_Price'}, inplace=True)
# df1からdtmとDA_Priceカラムのみを選択
df1_filtered = df1[['dtm', 'DA_Price']]
# df_date_onlyとdf1をdtmで結合
df1_merged = pd.merge(df_date_only, df1_filtered, on='dtm', how='left')
df2_merged = pd.merge(df1_merged, df2, on='dtm', how='left')
# ファイルを保存（これが入力データ）
df2_merged.to_csv('competition_price/data/API_DAP_SSP.csv', index=False)
print("Files merged and saved as 'API_DAP_SSP.csv'")

#train_dfの作成
# 入力データを読み込む
train_df = pd.read_csv('competition_price/data/API_DAP_SSP.csv')
#train_dfデータセットを整形
# 9日前の 'SS_Price' を新しい列として追加（432期前）
train_df['SS_Price_9days_ago'] = train_df['SS_Price'].shift(432)
#空白部分を後方置換
train_df['SS_Price_9days_ago'].bfill(inplace=True)
# 「DA_Price」に対しても時間遅れの特徴量を作成
# 48時間前の 'DA_Price' を新しい列として追加（96期前）
train_df['DA_Price_48h_ago'] = train_df['DA_Price'].shift(96)
#空白部分を後方置換
train_df['DA_Price_48h_ago'].bfill(inplace=True)
# 一週間前の 'DA_Price' を新しい列として追加（336期前）
train_df['DA_Price_1week_ago'] = train_df['DA_Price'].shift(336)
#空白部分を後方置換
train_df['DA_Price_1week_ago'].bfill(inplace=True)
# 新しい 'time' 列を作成
train_df['time'] = pd.to_datetime(train_df['dtm'])
# 年、月、日、時間を抽出
train_df['year'] = train_df['time'].dt.year
train_df['month'] = train_df['time'].dt.month
train_df['day'] = train_df['time'].dt.day
train_df['hour'] = train_df['time'].dt.hour + train_df['time'].dt.minute / 60
# 時間に関する周期的特徴を計算
train_df['hourCos'] = np.cos(train_df['hour'] * 2 * np.pi / 24)
train_df['hourSin'] = np.sin(train_df['hour'] * 2 * np.pi / 24)


# predict_dfデータセットの作成（train_dfから最後の48行（）を切り取る）
# 空のDataFrameを作成
predict_df = pd.DataFrame()
# train_dfの最後の49行を取得し、最初の1行を除外して48行を選択
last_48_rows = train_df.tail(49).iloc[:-1]
# train_dfの最後の48行のインデックスを取得
last_49_indices = train_df.tail(49).index
# これらのインデックスを使用して行を削除
train_df = train_df.drop(last_49_indices, axis=0)
# predict_dfを最後の48行で更新
predict_df = last_48_rows.copy()
# predict_dfから除外する列のリスト
columns_to_exclude = ['SS_Price', 'DA_Price']
# これらの列を除外
predict_df = predict_df.drop(columns_to_exclude, axis=1)
# 修正されたDataFrameをCSVファイルに保存（確認のため）
train_df.to_csv('competition_price/data/train_df.csv', mode='w')
# 修正されたDataFrameをCSVファイルに保存（確認のため）
predict_df.to_csv('competition_price/data/predict_df.csv', mode='w')


# quantilesを保存する辞書を作成
quantiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


#「SS_Price」予測モデル作成開始
quantile_losses_SS_Price = {q: [] for q in quantiles}

# 特徴量リスト
features_SS_Price = ['SS_Price_1week_ago', 'hourSin', 'hourCos']

# 量子回帰モデルを特徴量でフィットさせる
quantile_models_SS_Price = {}
for q in quantiles:
    formula = f'SS_Price ~ {" + ".join(features_SS_Price)}'
    quantile_models_SS_Price[q] = smf.quantreg(formula, train_df).fit(q=q)

# 空のDataFrameを作成（予測した結果を格納する）
predictions_df_SS_Price = pd.DataFrame(index=predict_df.index)

# predictions_dfに年、月、日、時間の列を追加
predictions_df_SS_Price['time'] = predict_df['time']
predictions_df_SS_Price['year'] = predict_df['time'].dt.year
predictions_df_SS_Price['month'] = predict_df['time'].dt.month
predictions_df_SS_Price['day'] = predict_df['time'].dt.day
predictions_df_SS_Price['hour'] = predict_df['time'].dt.hour + predict_df['time'].dt.minute / 60

#モデルを使い9個のQRを予測
for q in quantiles:
    model = quantile_models_SS_Price[q]
    pred = model.predict(predict_df[features_SS_Price])
    predictions_df_SS_Price[f'SS_Price_q_{q}'] = pred
    #予測完了を表示
    print(f"SS_Price_q_{q} predicted")


# 「DA_Price」モデル作成開始
quantile_losses_DA_Price = {q: [] for q in quantiles}

# 特徴量リスト
features_DA_Price = ['DA_Price_1week_ago', 'hourSin', 'hourCos']

#モデル作成
quantile_models_DA_Price = {}  # 名前を変更
for q in quantiles:
    formula = f'DA_Price ~ {" + ".join(features_DA_Price)}'
    quantile_models_DA_Price[q] = smf.quantreg(formula, train_df).fit(q=q)

# 「DA_Price」の予測結果を保存するためのDataFrameを作成
predictions_df_DA_Price = pd.DataFrame(index=predict_df.index)
predictions_df_DA_Price['time'] = predict_df['time']
predictions_df_DA_Price['year'] = predict_df['time'].dt.year
predictions_df_DA_Price['month'] = predict_df['time'].dt.month
predictions_df_DA_Price['day'] = predict_df['time'].dt.day
predictions_df_DA_Price['hour'] = predict_df['time'].dt.hour + predict_df['time'].dt.minute / 60

#モデルを使い9個のQRを予測
for q in quantiles:
    model_DA_Price = quantile_models_DA_Price[q]
    pred_DA_Price = model_DA_Price.predict(predict_df[features_DA_Price])
    predictions_df_DA_Price[f'DA_Price_q_{q}'] = pred_DA_Price
    #予測完了を表示
    print(f"DA_Price_q_{q} predicted")


# 「SS_Price」の予測結果を含むDataFrameと結合
predictions_df_final = predictions_df_SS_Price.join(predictions_df_DA_Price.drop(columns=['time', 'year', 'month', 'day', 'hour']))

# 修正された最終結果DataFrameをCSVファイルに保存
predictions_df_final.to_csv('competition_price/result/predict_price.csv', mode='w')
print("Predictions saved as 'predict_price.csv'")