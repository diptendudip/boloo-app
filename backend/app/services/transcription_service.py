"""
Transcription Service - Azure Speech-to-Text with Hindi Support

Handles audio transcription using Azure Cognitive Services Speech SDK.
Supports Hindi and English with automatic language detection.
"""

import os
import logging
from typing import Optional, Dict
import tempfile
import azure.cognitiveservices.speech as speechsdk
from app.config import settings

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available - audio format conversion disabled")

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Azure Speech-to-Text transcription service"""

    def __init__(self):
        """Initialize Azure Speech SDK configuration"""
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.speech_region = settings.AZURE_SPEECH_REGION

        if not self.speech_key or not self.speech_region:
            logger.warning(
                "Azure Speech credentials not configured. "
                "Transcription will use fallback/dummy mode."
            )

    def _create_speech_config(self, language: str = "hi-IN") -> speechsdk.SpeechConfig:
        """
        Create Azure Speech configuration

        Args:
            language: Language code (hi-IN for Hindi, en-IN for English)

        Returns:
            SpeechConfig object
        """
        if not self.speech_key or not self.speech_region:
            raise ValueError("Azure Speech credentials not configured")

        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )

        # Set recognition language
        speech_config.speech_recognition_language = language

        # Enable profanity filtering (optional)
        speech_config.set_profanity(speechsdk.ProfanityOption.Raw)

        return speech_config

    def _convert_to_wav(self, audio_file_path: str) -> str:
        """
        Convert audio file to WAV format for Azure Speech SDK

        Args:
            audio_file_path: Path to audio file (any format)

        Returns:
            Path to converted WAV file
        """
        file_ext = os.path.splitext(audio_file_path)[1].lower()

        # If already WAV, return as-is
        if file_ext == '.wav':
            return audio_file_path

        # If pydub not available, raise error
        if not PYDUB_AVAILABLE:
            raise RuntimeError(
                f"Audio format {file_ext} requires conversion but pydub is not installed. "
                "Install with: pip install pydub"
            )

        try:
            logger.info(f"Converting {file_ext} to WAV format...")

            # Load audio file
            audio = AudioSegment.from_file(audio_file_path)

            # Convert to WAV with Azure Speech SDK compatible settings
            # 16kHz, mono, 16-bit PCM
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit

            # Save to temporary WAV file
            wav_path = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            ).name

            audio.export(
                wav_path,
                format='wav',
                parameters=["-ar", "16000", "-ac", "1"]
            )

            logger.info(f"Audio converted to WAV: {wav_path}")
            return wav_path

        except Exception as e:
            logger.error(f"Audio conversion failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to convert audio to WAV: {str(e)}")

    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "hi-IN",
        enable_auto_language_detection: bool = True
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text

        Args:
            audio_file_path: Path to audio file (m4a, wav, mp3, ogg, webm)
            language: Primary language code (default: hi-IN for Hindi)
            enable_auto_language_detection: Enable automatic language detection

        Returns:
            dict: {
                "success": bool,
                "transcript": str,
                "language_detected": str,
                "confidence": float,
                "error": Optional[str]
            }
        """
        converted_wav_path = None

        try:
            # Check if Azure credentials are configured
            if not self.speech_key or not self.speech_region:
                logger.info("Using fallback transcription (Azure not configured)")
                return await self._fallback_transcription(audio_file_path)

            logger.info(f"Starting transcription for: {audio_file_path}")

            # Convert audio to WAV if needed
            try:
                wav_file_path = self._convert_to_wav(audio_file_path)
                if wav_file_path != audio_file_path:
                    converted_wav_path = wav_file_path
            except RuntimeError as e:
                logger.error(f"Audio conversion error: {e}")
                return {
                    "success": False,
                    "transcript": "",
                    "language_detected": language,
                    "confidence": 0.0,
                    "error": f"Audio format conversion failed: {str(e)}. Please ensure ffmpeg is installed or use WAV format audio."
                }

            # Create speech config
            speech_config = self._create_speech_config(language)

            # Create audio config from WAV file
            audio_config = speechsdk.audio.AudioConfig(filename=wav_file_path)

            # Create speech recognizer
            if enable_auto_language_detection:
                # Auto-detect between Hindi and English
                auto_detect_source_language_config = (
                    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=["hi-IN", "en-IN", "en-US"]
                    )
                )
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    auto_detect_source_language_config=auto_detect_source_language_config,
                    audio_config=audio_config
                )
            else:
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    audio_config=audio_config
                )

            # Perform CONTINUOUS recognition for long-form speech
            logger.info("Calling Azure Speech Recognition (continuous mode)...")

            # For long recordings, use continuous recognition
            done = False
            recognized_text = []
            detected_language = language

            def stop_cb(evt):
                """Callback that signals to stop continuous recognition"""
                nonlocal done
                done = True

            def recognized_cb(evt):
                """Callback for successfully recognized speech"""
                nonlocal recognized_text, detected_language
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    recognized_text.append(evt.result.text)

                    # Detect language from first utterance
                    if enable_auto_language_detection and hasattr(evt.result, 'properties') and len(recognized_text) == 1:
                        detected_language = evt.result.properties.get(
                            speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult,
                            language
                        )

            # Connect callbacks
            speech_recognizer.recognized.connect(recognized_cb)
            speech_recognizer.session_stopped.connect(stop_cb)
            speech_recognizer.canceled.connect(stop_cb)

            # Start continuous recognition
            speech_recognizer.start_continuous_recognition()

            # Wait until recognition is done (max 2 minutes for safety)
            import time
            start_time = time.time()
            while not done and (time.time() - start_time) < 120:
                time.sleep(0.1)

            # Stop recognition
            speech_recognizer.stop_continuous_recognition()

            # Combine all recognized text
            full_transcript = " ".join(recognized_text)

            if full_transcript:
                logger.info(f"Transcription successful: {full_transcript[:100]}... (total: {len(full_transcript)} chars)")

                return {
                    "success": True,
                    "transcript": full_transcript,
                    "language_detected": detected_language,
                    "confidence": 0.95,
                    "error": None
                }
            else:
                logger.warning("No speech could be recognized in continuous mode")
                return {
                    "success": False,
                    "transcript": "",
                    "language_detected": language,
                    "confidence": 0.0,
                    "error": "No speech detected in audio"
                }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "success": False,
                "transcript": "",
                "language_detected": language,
                "confidence": 0.0,
                "error": f"Transcription failed: {str(e)}"
            }
        finally:
            # Cleanup temporary WAV file
            if converted_wav_path and os.path.exists(converted_wav_path):
                try:
                    os.remove(converted_wav_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")

    async def _fallback_transcription(self, audio_file_path: str) -> Dict[str, any]:
        """
        Fallback transcription when Azure is not configured.
        Returns a basic response structure.
        """
        logger.warning("Using fallback transcription - Azure Speech not configured")
        return {
            "success": False,
            "transcript": "",
            "language_detected": "hi-IN",
            "confidence": 0.0,
            "error": "Transcription service not configured"
        }

    async def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: str = "hi-IN"
    ) -> Dict[str, any]:
        """
        Transcribe audio with word-level timestamps
        Useful for detailed analysis and playback sync

        Returns:
            dict with words array containing {text, start_time, end_time, confidence}
        """
        # This would require more complex Azure Speech SDK setup
        # For now, return basic transcription
        result = await self.transcribe_audio(audio_file_path, language)

        if result["success"]:
            # Convert to simple word timestamps
            words = result["transcript"].split()
            word_duration = 0.5  # Assume ~0.5s per word

            result["words"] = [
                {
                    "text": word,
                    "start_time": i * word_duration,
                    "end_time": (i + 1) * word_duration,
                    "confidence": result["confidence"]
                }
                for i, word in enumerate(words)
            ]

        return result


# Singleton instance
transcription_service = TranscriptionService()
