
import pandas as pd
import numpy as np
import requests
import pickle

NUM_FOLDS = 20

PARKS= {
        '阿寒摩周国立公園': 'AKAN',
        '十和田八幡平国立公園': 'TOWADA',
        '日光国立公園': 'NIKKO',
        '伊勢志摩国立公園': 'ISESHIMA',
        '大山隠岐国立公園': 'DAISEN',
        '阿蘇くじゅう国立公園': 'ASO',
        '霧島錦江湾国立公園': 'KIRISHIMA',
        '慶良間諸島国立公園': 'KERAMA',
        }

# weatherデータの紐付け用
PARK_POINT = {
            '熊本': '阿蘇くじゅう国立公園',
            '釧路': '阿寒摩周国立公園',
            '青森': '十和田八幡平国立公園',
            '十和田': '十和田八幡平国立公園',
            '渡嘉敷': '慶良間諸島国立公園',
            '高森': '阿蘇くじゅう国立公園',
            '鹿児島': '霧島錦江湾国立公園',
            '鳥羽': '伊勢志摩国立公園',
            '大田': '大山隠岐国立公園',
            '大山': '大山隠岐国立公園',
            '鹿角': '十和田八幡平国立公園',
            '日光': '日光国立公園'
            }

FEATS_EXCLUDED = ['index', 'datetime', 'visitors', 'year', 'park', 'weekofyear',
                  'month', 'weekday', 'park_month', 'park_japanese_holiday']

# One-hot encoding for categorical columns with get_dummies
def one_hot_encoder(df, nan_as_category = True):
    original_columns = list(df.columns)
    categorical_columns = [col for col in df.columns if df[col].dtype == 'object']
    df = pd.get_dummies(df, columns= categorical_columns, dummy_na= nan_as_category)
    new_columns = [c for c in df.columns if c not in original_columns]
    return df, new_columns

# correlationの高い変数を削除する機能
def removeCorrelatedVariables(data, threshold):
    corr_matrix = data.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))
    col_drop = [column for column in upper.columns if any(upper[column] > threshold) & ('visitors' not in column)]
    return col_drop

# 欠損値の率が高い変数を削除する機能
def removeMissingVariables(data, threshold):
    missing = (data.isnull().sum() / len(data)).sort_values(ascending = False)
    col_missing = missing.index[missing > 0.75]
    col_missing = [column for column in col_missing if 'visitors' not in column]

# LINE通知用
def line_notify(message):
    f = open('../input/line_token.txt')
    token = f.read()
    f.close
    line_notify_token = token.replace('\n', '')
    line_notify_api = 'https://notify-api.line.me/api/notify'

    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}  # 発行したトークン
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)
    print(message)

def save2pkl(path, df):
    f = open(path, 'wb')
    pickle.dump(df, f)
    f.close

def loadpkl(path):
    f = open(path, 'rb')
    out = pickle.load(f)
    return out
