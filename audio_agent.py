import asyncio
import os
import io
import wave
import pyaudio
from deepgram import DeepgramClient, PrerecordedOptions
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
            response = await self.deepgram.listen.asyncprerecorded.v("1").transcribe_file(
                payload, options
            )
            
            # Extract transcription
            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            print(f"Transcribed text: {transcript}")
            return transcript
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
    

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
    
    async def run_audio_session(self, recording_duration: int = 5):
        """
        Complete audio-to-agent pipeline
        """
        try:
            # Record audio
            audio_data = self.record_audio(recording_duration)
            
            # Transcribe audio
            transcript = await self.transcribe_audio(audio_data)
            
            if transcript:
                # Process with agent
                response = await self.process_with_agent(transcript)
                return response
            else:
                print("No speech detected in the audio.")
                return "No speech detected."
                
        except Exception as e:
            print(f"Error in audio session: {e}")
            return f"Error occurred: {e}"

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
    print("- LangGraph Agent: Processes your request and responds with text")
    print("\nCommands:")
    print("- Press Enter to start recording")
    print("- Type 'quit' to exit")
    print("- Type a number to set recording duration (seconds)")
    
    while True:
        user_input = input("\nPress Enter to record (or 'quit' to exit): ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        # Check if user specified duration
        recording_duration = 5  # default
        if user_input.isdigit():
            recording_duration = int(user_input)
            print(f"Recording duration set to {recording_duration} seconds")
            continue
        
        # Run audio session
        await agent.run_audio_session(recording_duration)

if __name__ == "__main__":
    asyncio.run(main())
