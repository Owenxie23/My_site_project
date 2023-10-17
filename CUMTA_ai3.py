from flask import Flask, request, render_template, jsonify, session
from flask_session import Session  # Import the Session extension
import smtplib
from email.mime.text import MIMEText
import openai
import pandas as pd
import numpy as np
#from ast import literal_eval
#from sklearn.ensemble import RandomForestClassifier
#from sklearn.model_selection import train_test_split
#from sklearn.metrics import classification_report, accuracy_score
#from openai.embeddings_utils import get_embedding
import datetime
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
app.config['SESSION_TYPE'] = 'filesystem'  # You can choose a different session type if needed
app.config['SECRET_KEY'] = 'jszqtktzsbqgbnbl'  # Replace with your secret key
Session(app)

# Define your OpenAI API key
api_key = os.getenv("cumta_ai")
openai.api_key = api_key

@app.route('/')
def index():
    return render_template('AI_Test_3.html')

def execute_openai_script(transcription):
    # Call your OpenAI script with the provided transcription

    from docx import Document

    def follow_email(transcription):
        follow_up_email = follow_up_email_extraction(transcription)
        return follow_up_email

    def follow_up_email_extraction(transcription):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are highly skilled AI trained in language comprehension and summarization, and you are also an AI expert in analyzing conversations and document writer in Chinese. You work at a mining engineering company. Please review the text and draft a thoughtful analysis document following this format:\n\
总结:\n\
\n\n\
检查结果：\n\
    设备安全隐患:\n\
    系统安全隐患:\n\
    环境安全隐患:\n\
    培训和安全意识:\n\
\n\n\
建议:\n\
\n\n\
下一步行动计划:"
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        return response['choices'][0]['message']['content']

    meeting_follow_up_email = follow_email(transcription)

    def next_ideas(transcription):
        solicitation_ideas = solicitation_ideas_extraction(transcription)
        return solicitation_ideas

    def solicitation_ideas_extraction(transcription):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI expert in mining engineering. You work at a mining engineering company. Please review the text and provide strategies or solutions for the strategic plan in Chinese."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        return response['choices'][0]['message']['content']

    next_step_ideas = next_ideas(transcription)

    def predict_score(meeting_follow_up_email):
        score = score_extraction(meeting_follow_up_email)
        return score

    def score_extraction(meeting_follow_up_email):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个经验丰富的矿山安全检查员, 做事小心谨慎, 请根据以下文章给出1至5的总体安全分数, 请只给我一个数值, 不用其他文字。"
                },
                {
                    "role": "user",
                    "content": meeting_follow_up_email
                }
            ]
        )
        return response['choices'][0]['message']['content']

    pred = predict_score(transcription)

    # Return the results as a dictionary
    results = {
        "analysis": meeting_follow_up_email,
        "next_step_ideas": next_step_ideas,
        "predicted_score": int(pred[0])
    }

    # Store the user data in a JSON file
    user_data = {
        "content": transcription,
        "userEmail": request.form['userEmail'],
        "analysis": meeting_follow_up_email,
        "next_step_ideas": next_step_ideas,
        "predicted_score": int(pred[0])
    }
    with open('user_data.json', 'a') as file:
        json.dump(user_data, file)

    return results

@app.route('/run-script', methods=['POST'])
def run_script():
    transcription = request.form['transcription']
    results = execute_openai_script(transcription)
    session['script_results'] = results  # Store the results in the session
    return jsonify(results)

@app.route('/send-email', methods=['POST'])
def send_email():
    recipient = request.form['userEmail']
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Your ReportGenius AI Report {timestamp}"

    # Get the script results from the session
    results = session.get('script_results', {})

    # Create the email content with the obtained results
    email_content = f"Analysis: {results.get('analysis', '')}\n" \
                    f"Next Steps: {results.get('next_step_ideas', '')}\n" \
                    f"Safety Score: {results.get('predicted_score', '')}"

    try:
        msg = MIMEText(email_content)
        msg['Subject'] = subject
        msg['From'] = "yyxie@usfca.edu"
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login("yyxie@usfca.edu", "jszq tktz sbqg bnbl")
            smtp_server.sendmail("yyxie@usfca.edu", recipient, msg.as_string())
        return jsonify({"message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
