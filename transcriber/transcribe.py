import sounddevice as sd
import numpy as np
import vosk
import json
import time
import queue
import sys
import os

def transcribe_audio():
    """
    Records audio from the microphone and transcribes it using Vosk.
    Returns the full transcribed text and handles speech detection more robustly.
    """
    # Audio Configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    BLOCK_SIZE = 8000  # Process audio in chunks
    RECORDING_TIMEOUT = 15  # Increased maximum recording time in seconds
    MIN_SILENCE_DURATION = 2.5  # Duration of silence to detect end of speech
    
    # Buffer to accumulate transcribed text
    accumulated_text = []
    
    # Check if Vosk model exists
    model_path = ("./vosk-model-small-en-in-0.4")
    if not os.path.exists(model_path):
        print(f"Error: Vosk model not found at {model_path}")
        print("Please download the model from https://alphacephei.com/vosk/models")
        return ""

    # Load Vosk Model
    try:
        model = vosk.Model(model_path)
        recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    except Exception as e:
        print(f"Error loading Vosk model: {str(e)}")
        return ""

    # Create a queue to store audio data
    q = queue.Queue()
    
    # Track silence for auto-stop
    last_speech_time = time.time()
    recording_start_time = time.time()
    has_speech = False
    silence_started = None

    # Callback function to process audio data
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
        q.put(bytes(indata))

    try:
        # Get default device info
        device_info = sd.query_devices(kind='input')
        print(f"Using device: {device_info['name']}")
        print("Recording... Speak now (will auto-stop after silence or press Ctrl+C to stop)")
        
        # Start recording
        with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback):
            print("Listening...")
            
            while True:
                # Check if we've reached the maximum recording time
                if time.time() - recording_start_time > RECORDING_TIMEOUT:
                    print("\nMaximum recording time reached.")
                    break
                
                # Process audio data
                if not q.empty():
                    data = q.get()
                    if recognizer.AcceptWaveform(data):
                        result_json = recognizer.Result()
                        result_dict = json.loads(result_json)
                        text = result_dict.get("text", "")
                        if text:
                            print(f"Recognized: {text}")
                            accumulated_text.append(text)
                            has_speech = True
                            last_speech_time = time.time()
                            silence_started = None
                    else:
                        # Check partial results for speech activity
                        partial = json.loads(recognizer.PartialResult())
                        if partial.get("partial", ""):
                            if not has_speech:
                                has_speech = True
                            last_speech_time = time.time()
                            silence_started = None
                        elif has_speech:
                            # Track silence after speech
                            current_time = time.time()
                            if silence_started is None:
                                silence_started = current_time
                            elif current_time - silence_started > MIN_SILENCE_DURATION:
                                print("\nDetected end of speech. Processing...")
                                break
                else:
                    # Short sleep to prevent CPU hogging
                    time.sleep(0.01)
            
            # Get final result
            final_result = json.loads(recognizer.FinalResult())
            final_text = final_result.get("text", "")
            if final_text:
                accumulated_text.append(final_text)
            
            # Combine all transcribed segments
            transcribed_text = " ".join(accumulated_text).strip()
            
            if not transcribed_text:
                print("No speech detected.")
                return ""
            
            print(f"Final transcription: {transcribed_text}")
            return transcribed_text

    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
        # Get what we have so far
        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get("text", "")
        if final_text:
            accumulated_text.append(final_text)
        return " ".join(accumulated_text).strip()
    except Exception as e:
        print(f"Error during recording: {str(e)}")
        print("Please check if your microphone is properly connected and enabled.")
        return ""


if __name__ == "__main__":
    text = transcribe_audio()
    if text:
        # Save the transcription to transcription.txt in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "transcription.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Transcription saved to {output_file}")