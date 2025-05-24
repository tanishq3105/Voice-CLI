import subprocess
import json
import sys
import os

# Step 1: Run the transcriber
def run_transcriber():
    print("[*] Running transcriber...")
    subprocess.run(["python", "transcriber/transcribe.py"], check=True)

    # Read the transcription output
    try:
        with open("transcriber/transcription.txt", "r") as f:
            transcription = f.read().strip()
            print("[+] Transcription:", transcription)
            return transcription
    except Exception as e:
        print(f"[!] Error reading transcription.txt: {e}")
        sys.exit(1)

def run_llm(transcription):
    print("[*] Running LLM backend...")
    import llm_backend.llm as llm_module
    result = llm_module.llm(transcription)
    print("[+] LLM result:", result)

    with open("shared_memory/command_output.txt", "w") as f:
        json.dump(result, f, indent=4)

def run_writer():
    print("[*] Writing to shared memory...")
    subprocess.run(["python", "shared_memory/writer.py"], check=True)

def run_executor():
    print("[*] Running C executor...")
    subprocess.run(["./executor/executor.out"], check=True)

if __name__ == "__main__":
    print("🔁 Voice-Controlled CLI Pipeline Starting...\n")
    transcription = run_transcriber()
    run_llm(transcription)
    run_writer()
    run_executor()
    print("\n✅ Pipeline execution completed.")
