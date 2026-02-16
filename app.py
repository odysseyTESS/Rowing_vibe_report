import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime

# --- 初期設定 ---
st.set_page_config(page_title="Boat-Vibe-Relayer", layout="centered", page_icon="🚣‍♂️")
st.title("🚣‍♂️ Boat-Vibe Relayer")
st.caption("2月の北大の寒さを、AIの力で乗り越える。")

# Secretsの取得
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SLACK_WEBHOOK_URL = st.secrets["SLACK_WEBHOOK_URL"]
except Exception:
    st.error("Secretsの設定（APIキー等）が見つかりません。")
    st.stop()

# --- Geminiのセットアップ ---
genai.configure(api_key=GEMINI_API_KEY)

# 【重要】404対策：利用可能なモデルを自動チェックして選択
try:
    # 安定版の名称を試行
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"モデルの初期化に失敗しました: {e}")

# --- UI部分 ---
uploaded_file = st.file_uploader("音声ファイル (m4a) をアップロード", type=["m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file)
    
    if st.button("報告書を生成＆Slackに送信"):
        with st.spinner("AIが解析中...（ここが踏ん張りどころです）"):
            try:
                # 1. 音声データの読み込み
                audio_data = uploaded_file.read()
                date_str = datetime.now().strftime("%Y/%m/%d")
                
                # 2. クリーンなプロンプト
                prompt = f"ボート部マネージャーとして、この音声（{date_str}の練習報告）をメニュー、目標、結果、振り返り（KPT形式）、雑談の順に整理して。署名や住所は不要。"

                # 3. 解析実行
                # 安全策：contentタイプを明示
                response = model.generate_content(
                    contents=[
                        {"role": "user", "parts": [
                            {"mime_type": "audio/m4a", "data": audio_data},
                            {"text": prompt}
                        ]}
                    ]
                )
                
                report_text = response.text
                
                # 4. Slack送信
                response_slack = requests.post(SLACK_WEBHOOK_URL, json={"text": report_text})
                
                if response_slack.status_code == 200:
                    st.success("✅ ついに成功！Slackに届きました！")
                    st.balloons()
                    st.text_area("生成内容:", value=report_text, height=200)
                else:
                    st.error(f"Slack送信失敗: {response_slack.status_code}")
                
            except Exception as e:
                st.error(f"エラー発生: {e}")
                # 404が出た場合、今使えるモデルを画面に表示する（デバッグ用）
                if "404" in str(e):
                    st.info("利用可能なモデルを検索中...")
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    st.write("あなたが今使えるモデル一覧:", available_models)
