import os
from gtts import gTTS
import subprocess
import tempfile
import shutil

def generate_interview_audio():
    # Create output directory if it doesn't exist
    os.makedirs("sample_interview", exist_ok=True)

    # Full script
    full_script = """
[Interviewer] Hello and welcome to our podcast. Today we're joined by Dr. Smith, an expert in artificial intelligence. Thank you for being here with us today.

[Interviewee] Thank you for having me. I'm excited to discuss the latest developments in AI research.

[Interviewer] Let's start with the basics. How would you explain artificial intelligence to someone who has no technical background?

[Interviewee] That's a great question. At its core, artificial intelligence is about creating systems that can perform tasks that typically require human intelligence. These tasks include learning from experience, understanding natural language, recognizing patterns, and making decisions.

[Interviewer] Interesting. And what are some of the most exciting recent developments in the field?

[Interviewee] Recently, we've seen tremendous progress in large language models and generative AI. These systems can now write essays, create images, and even code software based on simple text prompts. The capabilities have improved dramatically in just the past few years.

[Interviewer] Some people are concerned about the risks of advanced AI. What are your thoughts on that?

[Interviewee] It's a valid concern. Any powerful technology comes with risks. With AI specifically, we need to think about issues like bias in algorithmic decision-making, privacy concerns with data collection, and the potential for job displacement. The key is responsible development with proper oversight and regulation.

[Interviewer] Where do you see AI heading in the next five years?

[Interviewee] I think we'll see much better integration of AI into everyday tools and services. Healthcare diagnostics will improve, personalized education will become more accessible, and scientific research will accelerate. But the most exciting developments might be ones we haven't even imagined yet.

[Interviewer] That's fascinating. One final question: what advice would you give to young people interested in working in artificial intelligence?

[Interviewee] Learn the fundamentals of computer science and mathematics, but don't neglect the humanities. Some of the biggest challenges in AI aren't technical but ethical and social. We need diverse perspectives to build AI that works well for everyone.

[Interviewer] Thank you so much for sharing your insights with us today. This has been truly informative.

[Interviewee] It was my pleasure. Thank you for the thoughtful questions.
"""

    # Parse lines and alternate speakers
    lines = []
    for line in full_script.strip().split('\n'):
        line = line.strip()
        if line:
            if line.startswith('[Interviewer]'):
                lines.append(('interviewer', line.replace('[Interviewer]', '').strip()))
            elif line.startswith('[Interviewee]'):
                lines.append(('interviewee', line.replace('[Interviewee]', '').strip()))

    # Create a temporary directory for intermediate MP3s
    with tempfile.TemporaryDirectory() as tmpdir:
        filelist_path = os.path.join(tmpdir, "filelist.txt")
        mp3_paths = []

        # Generate audio clips and write to file list
        with open(filelist_path, "w") as f:
            for i, (speaker, text) in enumerate(lines):
                tld = 'us' if speaker == 'interviewer' else 'co.uk'
                slow = False if speaker == 'interviewer' else True
                tts = gTTS(text=text, lang='en', tld=tld, slow=slow)
                mp3_path = os.path.join(tmpdir, f"{speaker}_{i}.mp3")
                tts.save(mp3_path)
                f.write(f"file '{mp3_path}'\n")
                mp3_paths.append(mp3_path)

        # Output path
        output_path = "sample_interview/test_audio.wav"

        # Merge all mp3s into one wav using ffmpeg
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", filelist_path,
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_path
        ]
        print("🎙 Combining all speaker lines into final interview audio...")
        subprocess.run(cmd, check=True)

    print(f"✅ Interview audio generated at: {output_path}")
    return output_path

if __name__ == "__main__":
    try:
        generate_interview_audio()
    except Exception as e:
        print(f"❌ Error generating interview audio: {str(e)}")
