#Test script using Vader for sentiment analysis and Sentence-Transformers for answer relevance

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer, util

# Sentiment Analysis Function using VADER
def get_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment

# Answer Relevance Function using Sentence Transformers
def check_relevance(question, answer):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([question, answer])
    cosine_similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    return cosine_similarity.item()

def run_test():
    print("💬 Test Case 1: High Relevance + Negative Sentiment")
    question1 = "Tell me about a time you worked on a team project."
    answer1 = """
    I worked on a group project last semester where we had to build a machine learning model for classifying customer feedback.
    Unfortunately, my teammates didn’t contribute much, and I ended up doing most of the work alone. 
    There were constant delays, miscommunication, and even conflicts during meetings. 
    While I completed the project on time and got good results, the experience was mentally exhausting and frustrating.
    """
    sentiment1 = get_sentiment(answer1)
    relevance1 = check_relevance(question1, answer1)
    print("🧠 Sentiment:", sentiment1)
    print("🎯 Relevance Score:", relevance1)

    print("\n💬 Test Case 2: Moderate Relevance + Positive Sentiment")
    question2 = "How do you stay motivated at work?"
    answer2 = """
    I’m really passionate about technology, and I enjoy exploring new frameworks and tools during my free time.
    Recently, I built a fun side project using React and Flask. It was challenging but extremely rewarding.
    I also make sure to maintain a good work-life balance, which keeps me refreshed and productive.
    """
    sentiment2 = get_sentiment(answer2)
    relevance2 = check_relevance(question2, answer2)
    print("🧠 Sentiment:", sentiment2)
    print("🎯 Relevance Score:", relevance2)

if __name__ == "__main__":
    run_test()
