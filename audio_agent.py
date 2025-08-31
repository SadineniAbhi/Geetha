import asyncio
import os
import io
import wave
import pyaudio
import tempfile
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
from graph import graph

class AudioAgent:
    def __init__(self, deepgram_api_key: str):
        """
        Initialize the AudioAgent with Deepgram API key
        """
        self.deepgram = DeepgramClient(deepgram_api_key)
        
        # Audio recording parameters
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5  # Default recording duration
        
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
            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language="en"
            )
            
            # Create the audio source
            payload = {"buffer": audio_data}
            
            print("Transcribing audio...")
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
                # Process with agent
                response = await self.process_with_agent(transcript)
                
                # Convert response to speech and play it
                if enable_tts and response.strip():
                    speech_audio = await self.text_to_speech(response)
                    if speech_audio:
                        self.play_audio(speech_audio)
                    else:
                        print("Failed to generate speech - displaying text response only")
                
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
    
    print("🎤 Audio Agent initialized!")
    print("Features:")
    print("- Speech-to-Text: Converts your voice to text")
    print("- LangGraph Agent: Processes your request intelligently")
    print("- Text-to-Speech: Converts agent responses to speech")
    print("\nCommands:")
    print("- Press Enter to start recording with TTS")
    print("- Type 'text' to disable TTS (text-only mode)")
    print("- Type 'speech' to enable TTS (default)")
    print("- Type 'quit' to exit")
    print("- Type a number to set recording duration (seconds)")
    
    enable_tts = True  # Default TTS enabled
    recording_duration = 5  # Default duration
    
    while True:
        status = "🔊 TTS ON" if enable_tts else "📝 TEXT ONLY"
        user_input = input(f"\n[{status}] Press Enter to record (or command): ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif user_input.lower() == 'text':
            enable_tts = False
            print("TTS disabled - responses will be text-only")
            continue
        elif user_input.lower() == 'speech':
            enable_tts = True
            print("TTS enabled - responses will be spoken")
            continue
        elif user_input.isdigit():
            recording_duration = int(user_input)
            print(f"Recording duration set to {recording_duration} seconds")
            continue
        
        # Run audio session
        await agent.run_audio_session(recording_duration, enable_tts)

if __name__ == "__main__":
    asyncio.run(main())
