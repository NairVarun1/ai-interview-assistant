import os
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Load models
model = SentenceTransformer("all-MiniLM-L6-v2")
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

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

# Final rating calculator
def calculate_final_rating(sentiment_scores, relevance_scores):
    total_sentiment_score = sum(sentiment_scores)
    total_relevance_score = sum(relevance_scores)
    max_sentiment_score = len(sentiment_scores) * 3
    max_relevance_score = len(relevance_scores) * 2  # Updated max relevance per new scale

    sentiment_normalized = (total_sentiment_score / max_sentiment_score) * 5
    relevance_normalized = (total_relevance_score / max_relevance_score) * 5
    final_rating = sentiment_normalized + relevance_normalized
    return round(min(final_rating, 10), 1)

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

# Report generator with rejection if >=3 negative responses
def generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, output_path):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    candidate_name = "John Doe"
    final_rating = calculate_final_rating(sentiment_scores, relevance_scores)

    # ❌ Rejection condition: 3 or more negative answers
    if sentiment_summary["negative"] >= 3:
        verdict = "❌ NOT SELECTED (Too many negative answers)"
    else:
        verdict = "✅ SELECTED" if final_rating > 5 else "❌ NOT SELECTED"

    with open(output_path, "w") as f:
        f.write(f"Candidate Report – AI Interview Assistant\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"📅 Date: {date_str}\n🕒 Time: {time_str}\n👤 Candidate: {candidate_name}\n")
        f.write(f"Questions Answered: {len(results)}\n\n")

        for i, item in enumerate(results):
            f.write(f"{i+1}. ❓ {item['question']}\n")
            f.write(f"   💬 Candidate: {item['answer']}\n")
            f.write(f"   😊 Sentiment: {item['sentiment']}\n")
            f.write(f"   🎯 Relevance Score: {item['relevance']} (Similarity: {item['raw_similarity']:.2f})\n\n")

        f.write("📊 Summary\n")
        f.write(f"{'-'*40}\n")
        f.write(f"✔️ Positive Responses: {sentiment_summary['positive']}\n")
        f.write(f"✔️ Neutral Responses: {sentiment_summary['neutral']}\n")
        f.write(f"❌ Negative Responses: {sentiment_summary['negative']}\n")
        f.write(f"\n🏁 Verdict: {verdict}\n")
        f.write(f"\n🏆 Final Rating: {final_rating}/10\n")

    print(f"✅ Report saved to: {output_path}")

# Run script
if __name__ == "__main__":
    annotated_path = "annotated/sample_annotated.txt"
    output_path = "test_reports/test_report.txt"
    os.makedirs("test_reports", exist_ok=True)
    results, summary, relevance_scores, sentiment_scores = analyse_annotated_transcript(annotated_path)
    generate_report(results, summary, relevance_scores, sentiment_scores, output_path)
