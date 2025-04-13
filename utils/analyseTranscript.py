# utils/analyseTranscript.py

import os
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer, util

def load_annotated_transcript(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    dialogue = []
    for line in lines:
        if ':' in line:
            speaker, content = line.split(':', 1)
            dialogue.append((speaker.strip(), content.strip()))
    return dialogue

def analyse_transcript(transcript_path):
    dialogue = load_annotated_transcript(transcript_path)
    
    sentiment_analyzer = SentimentIntensityAnalyzer()
    model = SentenceTransformer('all-MiniLM-L6-v2')

    results = []
    last_question = None

    for speaker, content in dialogue:
        if speaker.lower() == 'interviewer':
            last_question = content
        elif speaker.lower() == 'candidate' and last_question:
            sentiment = sentiment_analyzer.polarity_scores(content)
            relevance = util.pytorch_cos_sim(
                model.encode(last_question),
                model.encode(content)
            ).item()

            results.append({
                "question": last_question,
                "answer": content,
                "sentiment": sentiment,
                "relevance": relevance
            })

    # Save results
    result_path = transcript_path.replace(".txt", "_analysis.json")
    with open(result_path, 'w') as f:
        json.dump(results, f, indent=4)

    print(f"✅ Analysis saved to {result_path}")
    return results
