import os
import re
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from textstat import flesch_reading_ease

# Load models
model = SentenceTransformer("all-MiniLM-L6-v2")
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
summarizer = pipeline("summarization", model="t5-base")

# Map label to human-readable sentiment
label_map = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

def get_sentiment_score(response):
    result = sentiment_pipeline(response)[0]
    label = result['label']
    sentiment_label = label_map[label]
    score = {"Positive": 3, "Neutral": 2, "Negative": 1}[sentiment_label]
    return score, sentiment_label

def get_relevance_score(answer, question):
    emb1 = model.encode(question, convert_to_tensor=True)
    emb2 = model.encode(answer, convert_to_tensor=True)
    relevance = float(util.pytorch_cos_sim(emb1, emb2).item())
    if relevance > 0.7:
        return 2, relevance
    elif 0.4 <= relevance <= 0.7:
        return 1, relevance
    else:
        return 0, relevance

def analyse_annotated_transcript(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()

    questions, answers = [], []
    current_question = ""
    current_answer = ""
    results = []

    for line in lines:
        line = line.strip()
        if line.startswith("Interviewer:"):
            if current_question and current_answer:
                questions.append(current_question)
                answers.append(current_answer)
                current_answer = ""
            current_question = line.replace("Interviewer:", "").strip()
        elif line.startswith("Candidate:"):
            current_answer = line.replace("Candidate:", "").strip()

    if current_question and current_answer:
        questions.append(current_question)
        answers.append(current_answer)

    sentiment_summary = {"positive": 0, "neutral": 0, "negative": 0}
    sentiment_scores = []
    relevance_scores = []

    for i in range(len(questions)):
        q = questions[i]
        a = answers[i]

        sentiment_score, sentiment_label = get_sentiment_score(a)
        sentiment_scores.append(sentiment_score)
        sentiment_summary[sentiment_label.lower()] += 1

        relevance_score, cos_sim = get_relevance_score(a, q)
        relevance_scores.append(relevance_score)

        results.append({
            "question": q,
            "answer": a,
            "sentiment": sentiment_label,
            "relevance": relevance_score,
            "raw_similarity": cos_sim
        })

    return results, sentiment_summary, relevance_scores, sentiment_scores

def extract_pros_and_cons(results):
    positive_answers = [r["answer"] for r in results if r["sentiment"] == "Positive"]
    negative_answers = [r["answer"] for r in results if r["sentiment"] == "Negative"]

    pros = []
    cons = []

    for ans in positive_answers:
        summary = summarizer("The candidate said: " + ans, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
        pros.append(f"• {summary}")

    for ans in negative_answers:
        summary = summarizer("The candidate said: " + ans, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
        cons.append(f"• {summary}")

    pros_text = " ".join(pros) if pros else "None"
    cons_text = " ".join(cons) if cons else "None"

    combined_summary = summarizer(f"Pros: {pros_text} Cons: {cons_text}", max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    return pros, cons, combined_summary

def evaluate_communication_skills(answers):
    clarity_scores = []
    confidence_scores = []

    for ans in answers:
        clarity = flesch_reading_ease(ans)
        clarity_scores.append(clarity)

        sentiment_result = sentiment_pipeline(ans)[0]
        confidence = sentiment_result['score']
        confidence_scores.append(confidence)

    avg_clarity = round(sum(clarity_scores) / len(clarity_scores), 2)
    avg_confidence = round(sum(confidence_scores) / len(confidence_scores), 2)

    return avg_clarity, avg_confidence

def generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, pros, cons, summary, output_path, avg_clarity, avg_confidence):
    now = datetime.now()
    with open(output_path, 'w') as f:
        f.write("Candidate Report – AI Interview Assistant\n")
        f.write("="*50 + "\n")
        f.write(f"📅 Date: {now.strftime('%Y-%m-%d')}\n")
        f.write(f"🕒 Time: {now.strftime('%H:%M')}\n\n")

        f.write(f"Questions Answered: {len(results)}\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"{i}. ❓ {r['question']}\n")
            f.write(f"   💬 Candidate: {r['answer']}\n")
            f.write(f"   😊 Sentiment: {r['sentiment']}\n")
            f.write(f"   🎯 Relevance Score: {relevance_scores[i-1]} (Similarity: {r['raw_similarity']:.2f})\n\n")

        f.write("🗣️ Communication Skill Analysis\n")
        f.write("-" * 40 + "\n")
        f.write(f"📖 Clarity Score : {avg_clarity} / 100\n")
        f.write(f"💪 Confidence Score : {avg_confidence} / 1\n\n")

        f.write("📊 Summary\n")
        f.write("-"*40 + "\n")
        f.write(f"✔️ Positive Responses: {sentiment_summary['positive']}\n")
        f.write(f"✔️ Neutral Responses: {sentiment_summary['neutral']}\n")
        f.write(f"❌ Negative Responses: {sentiment_summary['negative']}\n\n")

        final_rating = round(
            sentiment_summary['positive'] * 1.0 +
            sentiment_summary['neutral'] * 0.6 +
            sentiment_summary['negative'] * -0.5, 1
        )
        final_rating = max(min(final_rating, 10), 0)
        verdict = "SELECTED" if final_rating >= 6 else "NOT SELECTED"

        f.write(f"\n🏁 Verdict: {verdict}\n")
        f.write(f"🏆 Final Rating: {final_rating}/10\n\n")

        f.write("💡 Pros\n")
        f.write(f"{'-'*40}\n")
        for p in pros:
            f.write(f"{p}\n")

        f.write("\n⚠️ Cons\n")
        f.write(f"{'-'*40}\n")
        for c in cons:
            f.write(f"{c}\n")

        f.write("\n📝 Summary\n")
        f.write(f"{'-'*40}\n")
        f.write(f"{summary}\n")

    return verdict, final_rating

def generate_json_report(results, sentiment_summary, relevance_scores, sentiment_scores, pros, cons, summary, output_path, avg_clarity, avg_confidence, verdict, final_rating):
    now = datetime.now()
    finalVerdict = True if verdict == "SELECTED" else False

    report = {
        "candidate_report": {
            "date": now.strftime('%Y-%m-%d'),
            "time": now.strftime('%H:%M'),
            "questions_answered": len(results),
            "results": results,
            "communication_skill_analysis": {
                "clarity_score": avg_clarity,
                "confidence_score": avg_confidence
            },
            "summary": {
                "positive_responses": sentiment_summary['positive'],
                "neutral_responses": sentiment_summary['neutral'],
                "negative_responses": sentiment_summary['negative'],
                "final_rating": final_rating,
                "summary_text": summary
            },
            "verdict": finalVerdict,
            "pros": pros,
            "cons": cons
        }
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as json_file:
        json.dump(report, json_file, indent=4)

    print(f"\n✅ JSON Report saved at: {output_path}")

def save_meeting_reports(transcript_path, meeting_link):
    os.makedirs('recordings', exist_ok=True)
    meeting_id = re.sub(r'\W+', '_', meeting_link)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    report_folder = "test_reports"
    os.makedirs(report_folder, exist_ok=True)

    text_output_path = os.path.join(report_folder, f"{meeting_id}_{timestamp}_report.txt")
    json_output_path = os.path.join(report_folder, f"{meeting_id}_{timestamp}_report.json")

    results, sentiment_summary, relevance_scores, sentiment_scores = analyse_annotated_transcript(transcript_path)
    pros, cons, summary = extract_pros_and_cons(results)
    avg_clarity, avg_confidence = evaluate_communication_skills([r['answer'] for r in results])

    verdict, final_rating = generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, pros, cons, summary, text_output_path, avg_clarity, avg_confidence)
    generate_json_report(results, sentiment_summary, relevance_scores, sentiment_scores, pros, cons, summary, json_output_path, avg_clarity, avg_confidence, verdict, final_rating)

    print("Reports Generated Successfully !")

if __name__=="__main__":
    save_meeting_reports("recordings/meeting_audio_20250415_223508_annotated.txt","www.google.com")