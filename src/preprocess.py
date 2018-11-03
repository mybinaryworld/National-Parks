
import pandas as pd
import numpy as np
import gc

from utils import one_hot_encoder, PARK_POINT, PARKS

################################################################################
# 提供データを読み込み、データに前処理を施し、モデルに入力が可能な状態でファイル出力するモジュール。
# get_train_dataやget_test_dataのように、学習用と評価用を分けて、前処理を行う関数を定義してください。
################################################################################

# Preprocess train.tsv and test.tsv
def train_test(num_rows=None):
    print("Loading datasets...")
    # load datasets
    train_df = pd.read_csv('../input/train.tsv', sep='\t', nrows=num_rows)
    test_df = pd.read_csv('../input/test.tsv', sep='\t', nrows=num_rows)
    print("Train samples: {}, test samples: {}".format(len(train_df), len(test_df)))

    #testのtargetをnanにしときます
    test_df['visitors'] = np.nan

    # merge
    df = train_df.append(test_df[['datetime', 'park', 'visitors']]).reset_index()

    del train_df, test_df
    gc.collect()

    # 日付をdatetime型へ変換
    df['datetime'] = pd.to_datetime(df['datetime'])

    # 季節性の特徴量を追加
    df['day'] = df['datetime'].dt.day.astype(object)
    df['month'] = df['datetime'].dt.month.astype(object)
    df['weekday'] = df['datetime'].dt.weekday.astype(object)
    df['weekofyear'] = df['datetime'].dt.weekofyear.astype(object)
    df['day_month'] = df['day'].astype(str)+'_'+df['month'].astype(str)
    df['day_weekday'] = df['day'].astype(str)+'_'+df['weekday'].astype(str)
    df['day_weekofyear'] = df['day'].astype(str)+'_'+df['weekofyear'].astype(str)
    df['month_weekday'] = df['month'].astype(str)+'_'+df['weekday'].astype(str)
    df['month_weekofyear'] = df['month'].astype(str)+'_'+df['weekofyear'].astype(str)
    df['weekday_weekofyear'] = df['weekday'].astype(str)+'_'+df['weekofyear'].astype(str)

    df['park_day'] = df['park'].astype(str)+'_'+df['day'].astype(str)
    df['park_month'] = df['park'].astype(str)+'_'+df['month'].astype(str)
    df['park_weekday'] = df['park'].astype(str)+'_'+df['weekday'].astype(str)
    df['park_weekofyear'] = df['park'].astype(str)+'_'+df['weekofyear'].astype(str)

    # categorical変数を変換
    df_res, cat_cols = one_hot_encoder(df, nan_as_category=False)

    # stratify & mearge用
    df_res['park'] = df['park']
    df_res['weekofyear'] = df['weekofyear'].astype(int)
    df_res['year'] = df['datetime'].dt.year.astype(int)
    df_res['month'] = df['datetime'].dt.month.astype(int)

    return df_res

# Preprocess colopl.tsv
def colopl(num_rows=None):
    colopl = pd.read_csv('../input/colopl.tsv', sep='\t')

    # 1-9をとりあえず5で埋めます
    colopl['count'] = colopl['count'].replace('1-9', 5).astype(int)

    # 月ごとに集計
    colopl = colopl.pivot_table(index=['year', 'month'], columns='country_jp', values='count', aggfunc=sum)

    #　１ヶ月先へシフト
    colopl = colopl.shift()

    # カラム名を変更
    colopl.columns = ['COLOPL_'+ c for c in colopl.columns]

    return colopl

# Preprocess hotlink.tsv
def hotlink(num_rows=None):
    # load csv
    hotlink = pd.read_csv('../input/hotlink.tsv', sep='\t')

    # aggregate by datetime & keyword
    hotlink = hotlink.pivot_table(index='datetime', columns='keyword', values='count', aggfunc=sum)

    # indexをdatetime型に変換
    hotlink.index = pd.to_datetime(hotlink.index)

    # 1日先へシフト
    hotlink = hotlink.shift()

    # カラム名を変更
    hotlink.columns = ['HOTLINK_'+ c for c in hotlink.columns]

    return hotlink

# Preprocess nied_oyama.tsv
def nied_oyama(num_rows=None):
    nied_oyama = pd.read_csv('../input/nied_oyama.tsv', sep='\t')

    # 日付を追加
    nied_oyama['datetime'] = pd.DatetimeIndex(pd.to_datetime(nied_oyama['日時'])).normalize()

    # 公園名を追加
    nied_oyama['park'] = '大山隠岐国立公園'

    # 日付・公園ごとに集計
    nied_oyama = nied_oyama.groupby(['datetime', 'park']).mean()

    # 1日先へシフト
    nied_oyama = nied_oyama.shift()

    # カラム名を変更
    nied_oyama.columns = ['NIED_OYAMA_'+ c for c in nied_oyama.columns]

    return nied_oyama

# Preprocess nightley.tsv
def nightley(num_rows=None):
    nightley = pd.read_csv('../input/nightley.tsv', sep='\t')
    nightley.loc[:,'datetime'] = pd.to_datetime(nightley['datetime'])
    nightley['park'] = '日光国立公園'

    # 1日先へシフト
    nightley[['Japan_count','Foreign_count']] = nightley[['Japan_count','Foreign_count']].shift()

    # additional feature
    nightley['NIGHTLEY_F_J_RATIO'] = nightley['Foreign_count'] / nightley['Japan_count']
    nightley['NIGHTLEY_F_J_SUM'] = nightley['Foreign_count'] + nightley['Japan_count']

    # 日付と公園毎に集計
    nightley = nightley.groupby(['datetime', 'park']).mean()

    # カラム名を変更
    nightley.columns = ['NIGHTLEY_'+ c for c in nightley.columns]

    return nightley

# Preprocess weather.tsv
def weather(num_rows=None):
    weather = pd.read_csv('../input/weather.tsv', sep='\t')
    weather['datetime'] = pd.to_datetime(weather['年月日'])

    # 公園と紐付け
    weather['park'] = weather['地点'].map(PARK_POINT)

    # 不要なカラムを削除
    feats = [c for c in weather.columns if c not in ['年月日', '地点', '天気概況(昼:06時~18時)', '天気概況(夜:18時~翌日06時)']]

    # 日付と公園ごとに集計
    weather = weather[feats].groupby(['park', 'datetime']).mean()

    # １日前にシフト
    for park in PARKS.keys():
        weather.loc[park, :] = weather[weather.loc[park, :]==park].shift()

    # カラム名を変更
    weather.columns = ['WEATHER_'+ c for c in weather.columns]

    return weather

# Preprocess jorudan.tsv
def jorudan(num_rows=None):
    jorudan = pd.read_csv('../input/jorudan.tsv', sep='\t')

    return weather

if __name__ == '__main__':
    num_rows=10000
    # train & test
    df = train_test(num_rows)

    # colopl
#    colopl = colopl(num_rows)
#    df = df.join(colopl, how='left', on=[['datetime', 'park']])

    # hotlink
#    hotlink = hotlink(num_rows)
#    df = df.join(hotlink, how='left', on=[['datetime', 'park']])

    # nightley
    df = df.join(nightley(num_rows), how='left', on='datetime')

    # hotlink
    df = df.join(hotlink(num_rows), how='left', on='datetime')

    print(df)
