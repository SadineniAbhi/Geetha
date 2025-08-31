import asyncio
import os
import io
import wave
import pyaudio
import tempfile
import re
import threading
from queue import Queue
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
from graph import graph

class AudioAgent:
    def __init__(self, deepgram_api_key: str, stt_model: str = "nova-3"):
        """
        Initialize the AudioAgent with Deepgram API key
        """
        self.deepgram = DeepgramClient(deepgram_api_key)
        self.stt_model = stt_model
        
        # Audio recording parameters
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5  # Default recording duration
        
        # Streaming audio setup
        self.audio_queue = Queue()
        self.playback_active = False
        
        # STT Model configurations
        self.stt_models = {
            "nova-3": {
                "name": "Deepgram Nova-3",
                "description": "Latest model - 6.84% WER streaming, 5.26% batch",
                "strengths": "Highest accuracy, real-time multilingual support"
            },
            "nova-2": {
                "name": "Deepgram Nova-2", 
                "description": "Previous generation model",
                "strengths": "Fast and reliable"
            },
            "whisper-cloud": {
                "name": "Deepgram Whisper Cloud",
                "description": "OpenAI Whisper via Deepgram Cloud",
                "strengths": "Robust against noise, excellent with accents"
            },
            "enhanced": {
                "name": "Deepgram Enhanced",
                "description": "Balanced speed and accuracy",
                "strengths": "Good for general use cases"
            }
        }
        
        print(f"🎯 Using STT Model: {self.stt_models.get(stt_model, {}).get('name', stt_model)}")
        if stt_model in self.stt_models:
            print(f"   📊 {self.stt_models[stt_model]['description']}")
            print(f"   ⭐ {self.stt_models[stt_model]['strengths']}")
        
    def record_audio(self, duration: int = None) -> bytes:
        """
        Record audio from microphone
        """
        if duration:
            self.record_seconds = duration
            
        audio = pyaudio.PyAudio()
        
        print(f"Recording audio for {self.record_seconds} seconds...")
        print("Speak now!")
        
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk)
            frames.append(data)
        
        print("Recording finished!")
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Convert to bytes
        audio_data = b''.join(frames)
        return self._frames_to_wav_bytes(frames)
    
    def _frames_to_wav_bytes(self, frames) -> bytes:
        """
        Convert audio frames to WAV format bytes
        """
        wav_buffer = io.BytesIO()
        wav_file = wave.open(wav_buffer, 'wb')
        wav_file.setnchannels(self.channels)
        wav_file.setsampwidth(pyaudio.get_sample_size(self.format))
        wav_file.setframerate(self.rate)
        wav_file.writeframes(b''.join(frames))
        wav_file.close()
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio using Deepgram
        """
        try:
            # Configure transcription options with selected model
            options = PrerecordedOptions(
                model=self.stt_model,
                smart_format=True,
                language="en",
                punctuate=True,
                diarize=False,  # Set to True if you need speaker identification
                multichannel=False,
                alternatives=1,  # Get the best transcription
                profanity_filter=False,
                redact=False,
                encoding="linear16",
                sample_rate=16000
            )
            
            # Create the audio source
            payload = {"buffer": audio_data}
            
            print(f"🎯 Transcribing with {self.stt_models.get(self.stt_model, {}).get('name', self.stt_model)}...")
            response = await self.deepgram.listen.asyncrest.v("1").transcribe_file(
                payload, options
            )
            
            # Extract transcription
            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            print(f"Transcribed text: {transcript}")
            return transcript
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
    
    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using Deepgram TTS
        """
        try:
            print("Converting text to speech...")
            
            # Configure TTS options
            options = SpeakOptions(
                model="aura-asteria-en",  # High-quality voice model
                encoding="linear16",       # Audio format
                sample_rate=24000         # Supported sample rate for linear16
            )
            
            # Generate speech
            response = await self.deepgram.speak.asyncrest.v("1").stream_memory(
                {"text": text}, options
            )
            
            # Get audio data from the stream
            audio_data = response.stream.read()
            print("Text-to-speech conversion completed!")
            return audio_data
            
        except Exception as e:
            print(f"Error during text-to-speech: {e}")
            return b""
    
    async def stream_text_to_speech(self, text: str):
        """
        Stream text to speech by converting sentences immediately as they arrive
        """
        try:
            # Split text into sentences for immediate processing
            sentences = self._split_into_sentences(text)
            
            for sentence in sentences:
                if sentence.strip():
                    print(f"🔊 Converting: {sentence.strip()[:50]}...")
                    
                    # Configure TTS options for fast response
                    options = SpeakOptions(
                        model="aura-asteria-en",
                        encoding="linear16",
                        sample_rate=24000
                    )
                    
                    # Generate speech for this sentence
                    response = await self.deepgram.speak.asyncrest.v("1").stream_memory(
                        {"text": sentence.strip()}, options
                    )
                    
                    # Get audio data and add to queue for immediate playback
                    audio_chunk = response.stream.read()
                    if audio_chunk:
                        self.audio_queue.put(audio_chunk)
                        
        except Exception as e:
            print(f"Error during streaming TTS: {e}")
    
    def _split_into_sentences(self, text: str) -> list:
        """
        Split text into sentences for streaming TTS
        """
        # Split on sentence endings but keep meaningful chunks
        sentences = re.split(r'([.!?]+)', text)
        result = []
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i]
            ending = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = (sentence + ending).strip()
            
            if len(full_sentence) > 5:  # Only process meaningful sentences
                result.append(full_sentence)
        
        # Handle any remaining text without punctuation
        if sentences and not sentences[-1].strip() == "":
            remaining = sentences[-1].strip()
            if len(remaining) > 5:
                result.append(remaining)
        
        return result if result else [text]  # Fallback to original text
    
    def play_audio(self, audio_data: bytes, sample_rate: int = 24000):
        """
        Play audio data through speakers
        """
        if not audio_data:
            print("No audio data to play")
            return
            
        try:
            print("Playing audio...")
            
            # Save audio to temporary file and play
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write raw audio data as WAV
                wav_file = wave.open(temp_file.name, 'wb')
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
                wav_file.close()
                
                # Play using PyAudio
                audio = pyaudio.PyAudio()
                
                # Read the audio file
                wav_file = wave.open(temp_file.name, 'rb')
                
                # Open stream for playback
                stream = audio.open(
                    format=audio.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True
                )
                
                # Play audio in chunks
                chunk_size = 1024
                data = wav_file.readframes(chunk_size)
                while data:
                    stream.write(data)
                    data = wav_file.readframes(chunk_size)
                
                # Cleanup
                stream.close()
                audio.terminate()
                wav_file.close()
                
                # Remove temporary file
                os.unlink(temp_file.name)
                
                print("Audio playback completed!")
                
        except Exception as e:
            print(f"Error during audio playback: {e}")
    
    def start_streaming_playback(self):
        """
        Start streaming audio playback in a separate thread
        """
        if self.playback_active:
            return
            
        self.playback_active = True
        playback_thread = threading.Thread(target=self._streaming_playback_worker)
        playback_thread.daemon = True
        playback_thread.start()
    
    def stop_streaming_playback(self):
        """
        Stop streaming audio playback
        """
        self.playback_active = False
        # Clear any remaining audio in queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
    
    def _streaming_playback_worker(self):
        """
        Worker thread for streaming audio playback
        """
        audio = pyaudio.PyAudio()
        stream = None
        
        try:
            while self.playback_active:
                try:
                    # Get audio chunk from queue (timeout to check playback_active)
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    
                    if not stream:
                        # Initialize stream on first chunk
                        stream = audio.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=24000,
                            output=True,
                            frames_per_buffer=1024
                        )
                    
                    # Write raw audio data directly to stream
                    stream.write(audio_chunk)
                    
                except:
                    continue  # Timeout or empty queue, continue checking
                    
        except Exception as e:
            print(f"Error in streaming playback: {e}")
        finally:
            if stream:
                stream.close()
            audio.terminate()
    

    async def process_with_agent(self, text: str) -> str:
        """
        Process transcribed text with LangGraph agent
        """
        if not text.strip():
            return "No text was transcribed from the audio."
        
        print("Processing with LangGraph agent...")
        
        # Create message for the agent
        messages = [{"role": "user", "content": text}]
        
        # Stream response from agent
        response_chunks = []
        async for chunk, _ in graph.astream(
            {"messages": messages},
            {"configurable": {"thread_id": "audio_session"}},
            stream_mode="messages",
        ):
            if hasattr(chunk, 'content') and chunk.content:
                response_chunks.append(chunk.content)
                print(chunk.content, end="", flush=True)
        
        print("\n")  # New line after streaming
        return "".join(response_chunks)
    
    async def process_with_streaming_tts(self, text: str, enable_tts: bool = True):
        """
        Process with agent and stream TTS in real-time
        """
        if not text.strip():
            return "No text was transcribed from the audio."
        
        print("🤖 Processing with LangGraph agent...")
        
        # Start streaming audio playback
        if enable_tts:
            self.start_streaming_playback()
        
        # Create message for the agent
        messages = [{"role": "user", "content": text}]
        
        # Stream response from agent and process TTS in real-time
        response_chunks = []
        current_sentence = ""
        
        try:
            async for chunk, _ in graph.astream(
                {"messages": messages},
                {"configurable": {"thread_id": "audio_session"}},
                stream_mode="messages",
            ):
                if hasattr(chunk, 'content') and chunk.content:
                    chunk_content = chunk.content
                    response_chunks.append(chunk_content)
                    print(chunk_content, end="", flush=True)
                    
                    if enable_tts:
                        # Add to current sentence
                        current_sentence += chunk_content
                        
                        # Check if we have a complete sentence
                        if any(punct in current_sentence for punct in ['.', '!', '?']):
                            # Process this sentence immediately
                            await self._process_sentence_tts(current_sentence.strip())
                            current_sentence = ""
            
            # Process any remaining text
            if enable_tts and current_sentence.strip():
                await self._process_sentence_tts(current_sentence.strip())
            
            print("\n")  # New line after streaming
            
            # Wait a moment for audio to finish, then stop streaming
            if enable_tts:
                await asyncio.sleep(1)  # Short delay for last audio chunks
                self.stop_streaming_playback()
            
            return "".join(response_chunks)
            
        except Exception as e:
            if enable_tts:
                self.stop_streaming_playback()
            print(f"\nError in streaming processing: {e}")
            return "".join(response_chunks) if response_chunks else str(e)
    
    async def _process_sentence_tts(self, sentence: str):
        """
        Process a single sentence for immediate TTS
        """
        try:
            if len(sentence.strip()) > 3:  # Only process meaningful sentences
                options = SpeakOptions(
                    model="aura-asteria-en",
                    encoding="linear16",
                    sample_rate=24000
                )
                
                response = await self.deepgram.speak.asyncrest.v("1").stream_memory(
                    {"text": sentence}, options
                )
                
                audio_chunk = response.stream.read()
                if audio_chunk:
                    self.audio_queue.put(audio_chunk)
                    
        except Exception as e:
            print(f"TTS error for sentence: {e}")
    
    def set_stt_model(self, model: str):
        """
        Switch to a different STT model
        """
        if model in self.stt_models:
            self.stt_model = model
            print(f"🎯 Switched to STT Model: {self.stt_models[model]['name']}")
            print(f"   📊 {self.stt_models[model]['description']}")
            print(f"   ⭐ {self.stt_models[model]['strengths']}")
        else:
            print(f"❌ Unknown model: {model}")
            self.list_stt_models()
    
    def list_stt_models(self):
        """
        List all available STT models
        """
        print("\n🎤 Available STT Models:")
        for key, model in self.stt_models.items():
            status = "✅ CURRENT" if key == self.stt_model else "  "
            print(f"{status} {key}: {model['name']}")
            print(f"     📊 {model['description']}")
            print(f"     ⭐ {model['strengths']}")
            print()
    
    async def run_audio_session(self, recording_duration: int = 5, enable_tts: bool = True):
        """
        Complete audio-to-agent-to-speech pipeline
        """
        try:
            # Record audio
            audio_data = self.record_audio(recording_duration)
            
            # Transcribe audio
            transcript = await self.transcribe_audio(audio_data)
            
            if transcript:
                # Process with agent using streaming TTS for immediate response
                response = await self.process_with_streaming_tts(transcript, enable_tts)
                return response
            else:
                print("No speech detected in the audio.")
                no_speech_msg = "No speech detected."
                
                # Optionally speak the error message
                if enable_tts:
                    speech_audio = await self.text_to_speech(no_speech_msg)
                    if speech_audio:
                        self.play_audio(speech_audio)
                
                return no_speech_msg
                
        except Exception as e:
            error_msg = f"Error occurred: {e}"
            print(f"Error in audio session: {e}")
            
            # Optionally speak the error message
            if enable_tts:
                try:
                    speech_audio = await self.text_to_speech("Sorry, an error occurred during processing.")
                    if speech_audio:
                        self.play_audio(speech_audio)
                except:
                    pass  # If TTS fails, just continue
            
            return error_msg

async def main():
    """
    Main function to run the audio agent
    """
    # Get Deepgram API key from environment variable
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not deepgram_api_key:
        print("Please set your DEEPGRAM_API_KEY environment variable")
        print("You can get one from: https://console.deepgram.com/")
        return
    
    # Initialize audio agent
    agent = AudioAgent(deepgram_api_key)
    
    print("🎤 Real-Time Audio Agent initialized!")
    print("Features:")
    print("- ⚡ Streaming Speech-to-Text: Instant voice transcription")
    print("- 🤖 Streaming LangGraph Agent: Real-time intelligent processing")
    print("- 🔊 Streaming Text-to-Speech: Immediate audio response")
    print("- 🚀 Zero-delay conversation flow!")
    print("\nCommands:")
    print("- Press Enter to start streaming voice conversation")
    print("- Type 'text' to disable TTS (text-only mode)")
    print("- Type 'speech' to enable streaming TTS (default)")
    print("- Type 'models' to list STT models")
    print("- Type model name (nova-3, whisper-cloud, etc.) to switch STT")
    print("- Type 'quit' to exit")
    print("- Type a number to set recording duration (seconds)")
    
    enable_tts = True  # Default TTS enabled
    recording_duration = 5  # Default duration
    
    while True:
        status = "🚀 STREAMING TTS" if enable_tts else "📝 TEXT ONLY"
        user_input = input(f"\n[{status}] Press Enter to record (or command): ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif user_input.lower() == 'text':
            enable_tts = False
            print("🚀 Streaming TTS disabled - responses will be text-only")
            continue
        elif user_input.lower() == 'speech':
            enable_tts = True
            print("🔊 Streaming TTS enabled - real-time voice responses activated!")
            continue
        elif user_input.lower() == 'models':
            agent.list_stt_models()
            continue
        elif user_input.lower() in agent.stt_models.keys():
            agent.set_stt_model(user_input.lower())
            continue
        elif user_input.isdigit():
            recording_duration = int(user_input)
            print(f"Recording duration set to {recording_duration} seconds")
            continue
        
        # Run audio session
        await agent.run_audio_session(recording_duration, enable_tts)

if __name__ == "__main__":
    asyncio.run(main())
