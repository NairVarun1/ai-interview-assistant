import os
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import re

# Load models
model = SentenceTransformer("all-MiniLM-L6-v2")
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Map label to human-readable sentiment
label_map = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

# Sentiment Function
def get_sentiment_score(response):
    result = sentiment_pipeline(response)[0]
    label = result['label']
    sentiment_label = label_map[label]

    if sentiment_label == "Positive":
        return 3, sentiment_label
    elif sentiment_label == "Negative":
        return 1, sentiment_label
    else:
        return 2, sentiment_label

# Relevance Function with updated thresholds
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

# Extract candidate answers only
def extract_candidate_answers(text):
    pattern = r"Candidate: (.+)"
    return re.findall(pattern, text)

# Evaluate communication clarity and confidence
def evaluate_communication_skills(answers):
    from textstat import flesch_reading_ease

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

# Analysis function
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

# Extract pros and cons using summarization
def extract_pros_and_cons(results):
    positive_answers = [r["answer"] for r in results if r["sentiment"] == "Positive"]
    negative_answers = [r["answer"] for r in results if r["sentiment"] == "Negative"]

    pros_text = " ".join(positive_answers)
    cons_text = " ".join(negative_answers)

    pros_summary = summarizer(pros_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text'] if pros_text else "None"
    cons_summary = summarizer(cons_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text'] if cons_text else "None"

    pros = [f"• {pros_summary}"]
    cons = [f"• {cons_summary}"]

    return pros, cons

# Report generator
def generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, pros, cons, output_path, avg_clarity, avg_confidence):
    now = datetime.now()
    with open(output_path, 'w') as f:
        f.write("Candidate Report – AI Interview Assistant\n")
        f.write("="*50 + "\n")
        f.write(f"📅 Date: {now.strftime('%Y-%m-%d')}\n")
        f.write(f"🕒 Time: {now.strftime('%H:%M')}\n")
        f.write("👤\n")
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

        positive_weight = 1.0
        neutral_weight = 0.6
        negative_weight = -0.5
        final_rating = (
            sentiment_summary['positive'] * positive_weight +
            sentiment_summary['neutral'] * neutral_weight +
            sentiment_summary['negative'] * negative_weight
        )
        final_rating = round(max(min(final_rating, 10), 0), 1)

        verdict = "✅ SELECTED" if final_rating >= 6 else "❌ NOT SELECTED"
        f.write(f"\n🏁 Verdict: {verdict}\n")
        f.write(f"\n🏆 Final Rating: {final_rating}/10\n")

        f.write("\n💡 Pros\n")
        f.write(f"{'-'*40}\n")
        if pros:
            for p in pros:
                f.write(f"{p}\n")
        else:
            f.write("None identified.\n")

        f.write("\n⚠️ Cons\n")
        f.write(f"{'-'*40}\n")
        if cons:
            for c in cons:
                f.write(f"{c}\n")
        else:
            f.write("None identified.\n")

# Main execution
if __name__ == "__main__":
    annotated_path = "annotated/sample_annotated.txt"
    output_path = "test_reports/test_report.txt"
    os.makedirs("test_reports", exist_ok=True)

    results, summary, relevance_scores, sentiment_scores = analyse_annotated_transcript(annotated_path)
    pros, cons = extract_pros_and_cons(results)
    avg_clarity, avg_confidence = evaluate_communication_skills([r["answer"] for r in results])

    print("\n=== ✅ Pros ===")
    for p in pros:
        print(p)

    print("\n=== ❌ Cons ===")
    for c in cons:
        print(c)

    print("\n=== 🗣️ Communication Skill Analysis ===")
    print(f"📖 Clarity Score : {avg_clarity} / 100")
    print(f"💪 Confidence Score : {avg_confidence} / 1")    

    generate_report(results, summary, relevance_scores, sentiment_scores, pros, cons, output_path, avg_clarity, avg_confidence)
