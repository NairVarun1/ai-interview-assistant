import os
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Load models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

# LLM for summary (e.g., Mistral-7B-Instruct or TinyLlama for faster inference)
llm_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(llm_model)
model = AutoModelForCausalLM.from_pretrained(llm_model, device_map="auto", torch_dtype="auto")


label_map = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

def get_sentiment_score(response):
    result = sentiment_pipeline(response)[0]
    label = result['label'].upper()
    sentiment_label = label_map.get(label, "Neutral")

    if sentiment_label == "Positive":
        return 3, sentiment_label
    elif sentiment_label == "Negative":
        return 1, sentiment_label
    else:
        return 2, sentiment_label

def get_relevance_scores_batch(questions, answers):
    q_embeddings = embedding_model.encode(questions, convert_to_tensor=True)
    a_embeddings = embedding_model.encode(answers, convert_to_tensor=True)

    relevance_scores = []
    similarities = []

    for q_emb, a_emb in zip(q_embeddings, a_embeddings):
        relevance = float(util.pytorch_cos_sim(q_emb, a_emb).item())
        similarities.append(relevance)
        if relevance > 0.7:
            relevance_scores.append(2)
        elif 0.4 <= relevance <= 0.7:
            relevance_scores.append(1)
        else:
            relevance_scores.append(0)

    return relevance_scores, similarities

def generate_llm_summary(results):
    chat_prompt = "You are an AI interview assistant. Based on the following transcript of Q&A, provide a summary of the candidate's performance and whether they should be selected or not.\n\n"
    for i, item in enumerate(results):
        chat_prompt += f"Q{i+1}: {item['question']}\nA{i+1}: {item['answer']}\nSentiment: {item['sentiment']}, Relevance Score: {item['relevance']}, Similarity: {item['raw_similarity']:.2f}\n\n"

    chat_prompt += "Now provide a summary and your final recommendation (Selected / Not Selected) with reasoning.\n"

    inputs = tokenizer(chat_prompt, return_tensors="pt", truncation=True, max_length=4096).to(model.device)
    output = model.generate(**inputs, max_new_tokens=300, temperature=0.7, do_sample=True)
    summary = tokenizer.decode(output[0], skip_special_tokens=True)

    # Extract only the generated part after prompt
    generated_text = summary[len(chat_prompt):].strip()
    return generated_text

def analyse_annotated_transcript(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()

    questions, answers = [], []
    current_question, current_answer = "", ""

    for line in lines:
        line = line.strip()
        if ":" not in line or not line.split(":", 1)[1].strip():
            continue

        speaker_label, text = line.split(":", 1)
        speaker_label, text = speaker_label.strip(), text.strip()

        if "Interviewer" in speaker_label:
            if current_question and current_answer:
                questions.append(current_question)
                answers.append(current_answer)
                current_answer = ""
            current_question = text
        elif "Candidate" in speaker_label:
            current_answer = text

    if current_question and current_answer:
        questions.append(current_question)
        answers.append(current_answer)

    if not questions or not answers:
        print("⚠️ No valid Q&A pairs found in transcript.")
        return [], {}, [], []

    sentiment_summary = {"positive": 0, "neutral": 0, "negative": 0}
    sentiment_scores = []
    results = []

    for a in answers:
        sentiment_score, sentiment_label = get_sentiment_score(a)
        sentiment_scores.append(sentiment_score)
        sentiment_summary[sentiment_label.lower()] += 1

    relevance_scores, similarities = get_relevance_scores_batch(questions, answers)

    for i in range(len(questions)):
        results.append({
            "question": questions[i],
            "answer": answers[i],
            "sentiment": ["Negative", "Neutral", "Positive"][sentiment_scores[i]-1],
            "relevance": relevance_scores[i],
            "raw_similarity": similarities[i]
        })

    return results, sentiment_summary, relevance_scores, sentiment_scores

def generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, output_path, candidate_name="John Doe"):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    final_rating = round((sum(sentiment_scores) / (len(sentiment_scores) * 3) * 5 if sentiment_scores else 0) +
                         (sum(relevance_scores) / (len(relevance_scores) * 2) * 5 if relevance_scores else 0), 1)

    summary_verdict = generate_llm_summary(results)

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
        f.write(f"✔️ Positive Responses: {sentiment_summary.get('positive', 0)}\n")
        f.write(f"✔️ Neutral Responses: {sentiment_summary.get('neutral', 0)}\n")
        f.write(f"❌ Negative Responses: {sentiment_summary.get('negative', 0)}\n")
        f.write(f"\n🏆 Final Rating: {final_rating}/10\n")
        f.write(f"\n🧠 LLM Summary & Verdict:\n{summary_verdict}\n")

    print(f"✅ Report saved to: {output_path}")

    json_path = output_path.replace(".txt", ".json")
    with open(json_path, "w") as jf:
        json.dump({
            "candidate_name": candidate_name,
            "date": date_str,
            "time": time_str,
            "questions_answered": len(results),
            "summary": sentiment_summary,
            "final_rating": final_rating,
            "responses": results,
            "llm_summary": summary_verdict
        }, jf, indent=4)
    print(f"📁 JSON report saved to: {json_path}")

def get_latest_transcript(folder="annotated"):
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]
    if not files:
        raise FileNotFoundError("No annotated .txt files found in 'annotated/'")
    return max(files, key=os.path.getmtime)

if __name__ == "__main__":
    transcript_path = get_latest_transcript("annotated")
    print(f"📄 Analysing file: {transcript_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"report_{timestamp}.txt"
    output_path = os.path.join("test_reports", output_file)
    os.makedirs("test_reports", exist_ok=True)

    results, summary, rel_scores, sent_scores = analyse_annotated_transcript(transcript_path)
    if results:
        generate_report(results, summary, rel_scores, sent_scores, output_path)
    else:
        print("❌ Report generation skipped due to no valid responses.")
