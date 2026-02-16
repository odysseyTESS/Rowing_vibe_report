import streamlit as st
import google.generativeai as genai
import requests
import datetime

# --- 初期設定 ---
st.set_page_config(page_title="Boat-Vibe-Relayer", layout="centered", page_icon="🚣‍♂️")
st.title("🚣‍♂️ Boat-Vibe Relayer")
st.caption("北14条の寒さにも負けず、音声一本でSlack報告を完了させます。")

# Secretsから鍵を安全に読み込む
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SLACK_WEBHOOK_URL = st.secrets["SLACK_WEBHOOK_URL"]

# --- Geminiのセットアップ ---
genai.configure(api_key=GEMINI_API_KEY)
# あなたが見つけた最新モデルの指定方法を採用
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

# --- UI部分 ---
uploaded_file = st.file_uploader("音声ファイル (m4a) をアップロード", type=["m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file)
    
    if st.button("報告書を生成＆Slackに送信"):
        with st.spinner("AIが練習内容を解析中..."):
            try:
                # 1. 音声データの読み込み
                audio_data = uploaded_file.read()
                
                # 2. 魂のプロンプト（北大ボート部専用）
                prompt = """
                あなたは北海道大学ボート部の優秀なマネージャー兼、将来の起業家を支えるメンターです。
                選手の練習後の独り言（音声）を聞き取り、指定のフォーマットに正確に落とし込んでください。

                【ルール】
                1. 日付は今日の日付と現在の曜日を「2/16 ( Mon )」のような形式で。
                2. 音声から『メニュー』『目標』『結果』を抽出してください。
                3. 『振り返り』はKPT形式（Keep: 良かった点、Problem: 課題、Try: 次にやること）で整理。
                4. ボート用語（UT, B1, B2, RPE, エルゴ, 艇庫など）を文脈から正しく判断して漢字・英語に変換してください。
                5. 最後に『（さらに何かあれば）』として、雑談やエピソードを詳しく記載。
                6. 文末の署名は「三浦尚史」としてください。

                【出力フォーマット】
                日付 [日付] ( [曜日] )
                【メニュー】
                [内容]

                【目標】
                [内容]

                【結果】
                [内容]

                【振り返り】
                K:
                P:
                T:

                （さらに何かあれば）
                [内容]

                

                # 3. Geminiによる解析
                response = model.generate_content([
                    prompt,
                    {"mime_type": "audio/m4a", "data": audio_data}
                ])
                
                report_text = response.text
                
                # 4. Slackへ送信
                slack_data = {"text": report_text}
                response_slack = requests.post(SLACK_WEBHOOK_URL, json=slack_data)
                
                if response_slack.status_code == 200:
                    st.success("✅ Slackへの投稿に成功しました！お疲れ様です！")
                    st.text_area("生成された内容（確認用）:", value=report_text, height=300)
                else:
                    st.error(f"Slack送信エラー: {response_slack.status_code}")
                
            except Exception as e:
                st.error(f"解析中にエラーが発生しました。時間を置いて試してください: {e}")
