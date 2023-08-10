import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk
import plotly.express as px
import locale

df_jp_ind = pd.read_csv('/Users/orfevre/Desktop/streamlit_app/data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv',encoding='shift_jis')
df_jp_category = pd.read_csv('/Users/orfevre/Desktop/streamlit_app/data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv',encoding='shift_jis')
df_pref_ind = pd.read_csv('/Users/orfevre/Desktop/streamlit_app/data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv',encoding='shift_jis')
df_pref_category = pd.read_csv('/Users/orfevre/Desktop/streamlit_app/data/雇用_医療福祉_一人当たり賃金_都道府県_大分類.csv',encoding='shift_jis')

st.title('日本の賃金ダッシュボード')


st.subheader('◾2019年　１人あたり賃金ヒートマップ')

jp_lat_lon = pd.read_csv('/Users/orfevre/Desktop/streamlit_app/data/pref_lat_lon.csv')
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name':'都道府県名'})

# df_jp_indを条件抽出する（年齢ごと＋集計年）
df_pref_map = df_pref_ind[(df_pref_ind['年齢']=='年齢計') & (df_pref_ind['集計年']==2019)]

# 2つのデータフレームを結合する（merge）
df_pref_map = pd.merge(df_pref_map, jp_lat_lon, on='都道府県名')

#一人あたり賃金を正規化して列を加える（正規化：x-x.min/x.max-x.min）
df_pref_map['一人当たり賃金（相対値）'] = (df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())\
    /(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min())

# pydendikでグラフを表示するための４つの設定
# ❶viewを設定する
view = pdk.ViewState(
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,#拡大する値
    pitch=40.5 #角度
)
# ❷layerを設定する
layer = pdk.Layer(
    'HeatmapLayer', #ヒートマップ
    data=df_pref_map,
    opacity=0.4, #不透明度の設定
    get_position=['lon','lat'], #経度、緯度の順に設定しないとエラーになるよ
    threshold=0.3,#閾値を設定
    get_weight='一人当たり賃金（相対値）'#複数のカラムがあった場合にどの値を使ウカを設定
)

#❸レンダリングする（画像を可視化して表示すること）
layer_map = pdk.Deck(layers=layer,
                 initial_view_state=view)

#❹streamlitでpydeckの図を表示する
st.pydeck_chart(layer_map)

#チェックボックスを表示する
show_df = st.checkbox('データを表示する')

#チェックボックスにチェックされた場合に元データを表示する
if show_df == True:
    st.write(df_pref_map)
    
#県別、全国の一人あたり賃金の推移を折れ線グラフで表示する-----------------------------------------


st.subheader('◾️１人あたり賃金の推移（折れ線グラフ）')

# ロケールを設定（英語ロケールを使用）
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# データフレームの各カラムからカンマを取り除く
df_jp_ind['集計年'] = df_jp_ind['集計年'].astype(str).replace(',', '')

#全国の賃金データを年齢計で抽出
df_ts_mean = df_jp_ind[(df_jp_ind['年齢']=='年齢計')]
df_ts_mean['集計年'] = df_ts_mean['集計年'].astype(str).replace(',', '')

#わかりやすいようにカラムの名前を変えておく
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）':'全国_一人当たり賃金（万円）'})

# 都道府県別にデータを抽出
df_pref_mean = df_pref_ind[(df_pref_ind['年齢']=='年齢計')]
df_pref_mean['集計年'] = df_pref_mean['集計年'].astype(str).replace(',', '')
# ユニークな値（都道府県名）を抽出する
pref_list = df_pref_mean['都道府県名'].unique()

# 都道府県を選択できるようにする
option_pref = st.selectbox('都道府県',
             (pref_list))

df_pref_mean = df_pref_mean[df_pref_mean['都道府県名']==option_pref]

#棒グラフを書くために、２つのデータをマージする
df_mean_line = pd.merge(df_ts_mean,df_pref_mean, on='集計年')


#棒グラフを書くために必要なカラムに絞る
df_mean_line = df_mean_line[['集計年','全国_一人当たり賃金（万円）','一人当たり賃金（万円）']]
df_mean_line = df_mean_line.set_index('集計年')
st.line_chart(df_mean_line)

st.subheader('◾️年齢別の1人あたり賃金推移 単位：百万円')
#------------------------------------------------------------------------------------------

#ここからバブルチャートを作成-------------------------------------------------------------------

df_mean_bubble = df_jp_ind[(df_jp_ind['年齢'] != '年齢計')]
fig = px.scatter(df_mean_bubble,
                 x='一人当たり賃金（万円）',#x軸を指定
                 y='年間賞与その他特別給与額（万円）',#y軸を指定
                 range_x = [150,700],#xの範囲を指定
                 range_y = [0,150],#yの範囲を指定
                 size = '所定内給与額（万円）',#バブルで表す項目を指定
                 size_max=38,#バブルの大きさの最大値を指定（指定しなくても自動で設定してくれる）
                 color = '年齢',#バブルの色をどうするか。今回は年齢を指定
                 animation_frame='集計年',# アニメーションの推移を何を基準にするか。今回は年単位の推移を見たい
                 animation_group='年齢')#グループ設定するのは今回年齢
st.plotly_chart(fig)

#-出典を記載-------------------------------------------------------------------------------------
st.text('出典：RESAS')
st.text('本サイトはRESASから取得したデータをもとに加工して作成')
#-----------------------------------------------------------------------------------------






