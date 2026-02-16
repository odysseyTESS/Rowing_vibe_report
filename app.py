import streamlit as st
import google.generativeai as genai
import requests

# --- 初期設定 ---
st.set_page_config(page_title="Boat-Vibe-Relayer", layout="centered", page_icon="🚣‍♂️")
st.title("🚣‍♂️ Boat-Vibe Relayer")
st.caption("音声で伝える、ボート部の新しい報告スタイル。")

# Secretsから鍵を安全に読み込む
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SLACK_WEBHOOK_URL = st.secrets["SLACK_WEBHOOK_URL"]

# --- Geminiのセットアップ ---
genai.configure(api_key=GEMINI_API_KEY)

# 404エラー対策：フルパスでモデルを指定します
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

# --- UI部分 ---
uploaded_file = st.file_uploader("音声ファイル (m4a) をアップロード", type=["m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file)
    
    if st.button("報告書を生成＆Slackに送信"):
        with st.spinner("AIが練習内容を解析中..."):
            try:
                # 1. 音声データの読み込み
                audio_data = uploaded_file.read()
                
                # 2. 魂のプロンプト（完全クリーン版）
                # 特定の個人名や場所への言及を削除しました
                prompt = """
あなたはボート部の優秀なマネージャーです。
選手の練習後の独り言（音声）を聞き取り、指定のフォーマットに正確に落とし込んでください。

【ルール】
1. 日付は今日の日付と現在の曜日を「2/16 ( Mon )」のような形式で。
2. 音声から『メニュー』『目標』『結果』を抽出してください。
3. 『振り返り』はKPT形式（Keep: 良かった点、Problem: 課題、Try: 次にやること）で整理。
4. ボート用語（UT, B1, B2, RPE, エルゴ, 艇庫など）を文脈から正しく判断して漢字・英語に変換してください。
5. 最後に『（さらに何かあれば）』として、雑談やエピソードを記載してください。

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
"""

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
                    st.success("✅ Slackへの投稿に成功しました！")
                    st.text_area("生成された内容（確認用）:", value=report_text, height=300)
                else:
                    st.error(f"Slack送信エラー: {response_slack.status_code}")
                
            except Exception as e:
                # 万が一また404が出る場合に備え、利用可能なモデルを表示するヒントを追加
                st.error(f"エラーが発生しました: {e}")
                st.info("APIキーの設定や、Google AI StudioでGemini APIが有効になっているか確認してください。")

