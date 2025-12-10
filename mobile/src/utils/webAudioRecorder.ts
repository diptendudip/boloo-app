/**
 * Web Audio Recorder - Native browser MediaRecorder implementation
 *
 * Uses the Web MediaRecorder API for reliable audio recording on browsers.
 * This is a fallback for expo-audio which may not work correctly on web.
 */

export interface WebAudioRecorderState {
  isRecording: boolean;
  duration: number;
  uri: string | null;
}

class WebAudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private startTime: number = 0;
  private _isRecording: boolean = false;
  private _uri: string | null = null;
  private _duration: number = 0;

  get isRecording(): boolean {
    return this._isRecording;
  }

  get uri(): string | null {
    return this._uri;
  }

  get currentTime(): number {
    if (this._isRecording && this.startTime > 0) {
      return (Date.now() - this.startTime) / 1000;
    }
    return this._duration;
  }

  async requestPermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop immediately - we just wanted to check permission
      stream.getTracks().forEach(track => track.stop());
      console.log('[WebAudioRecorder] Permission granted');
      return true;
    } catch (error) {
      console.error('[WebAudioRecorder] Permission denied:', error);
      return false;
    }
  }

  async prepareToRecordAsync(): Promise<void> {
    console.log('[WebAudioRecorder] Preparing to record...');

    // Clean up any existing recording
    this.cleanup();

    try {
      // Get audio stream
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        }
      });

      // Determine best supported MIME type
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/mpeg',
      ];

      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          console.log('[WebAudioRecorder] Using MIME type:', mimeType);
          break;
        }
      }

      if (!selectedMimeType) {
        console.warn('[WebAudioRecorder] No specific MIME type supported, using default');
      }

      // Create MediaRecorder with options
      const options: MediaRecorderOptions = selectedMimeType
        ? { mimeType: selectedMimeType }
        : {};

      this.mediaRecorder = new MediaRecorder(this.stream, options);
      this.audioChunks = [];

      // Handle data available
      this.mediaRecorder.ondataavailable = (event) => {
        console.log('[WebAudioRecorder] Data available, size:', event.data.size);
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      // Handle recording stop
      this.mediaRecorder.onstop = () => {
        console.log('[WebAudioRecorder] Recording stopped, chunks:', this.audioChunks.length);
        this._isRecording = false;
        this._duration = (Date.now() - this.startTime) / 1000;

        // Create blob from chunks
        const mimeType = this.mediaRecorder?.mimeType || 'audio/webm';
        const blob = new Blob(this.audioChunks, { type: mimeType });
        console.log('[WebAudioRecorder] Created blob, size:', blob.size, 'type:', blob.type);

        // Create blob URL
        this._uri = URL.createObjectURL(blob);
        console.log('[WebAudioRecorder] Created URI:', this._uri);
      };

      this.mediaRecorder.onerror = (event) => {
        console.error('[WebAudioRecorder] Error:', event);
        this._isRecording = false;
      };

      console.log('[WebAudioRecorder] Prepared successfully');
    } catch (error) {
      console.error('[WebAudioRecorder] Failed to prepare:', error);
      throw error;
    }
  }

  record(): void {
    if (!this.mediaRecorder) {
      console.error('[WebAudioRecorder] Not prepared - call prepareToRecordAsync first');
      return;
    }

    if (this.mediaRecorder.state === 'recording') {
      console.warn('[WebAudioRecorder] Already recording');
      return;
    }

    console.log('[WebAudioRecorder] Starting recording...');
    this.audioChunks = [];
    this._uri = null;
    this.startTime = Date.now();
    this._isRecording = true;

    // Request data every 100ms to ensure we get chunks
    this.mediaRecorder.start(100);
    console.log('[WebAudioRecorder] Recording started');
  }

  async stop(): Promise<string | null> {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || this.mediaRecorder.state !== 'recording') {
        console.warn('[WebAudioRecorder] Not recording');
        resolve(this._uri);
        return;
      }

      console.log('[WebAudioRecorder] Stopping recording...');

      // Set up one-time listener for when stop completes
      const originalOnStop = this.mediaRecorder.onstop;
      this.mediaRecorder.onstop = (event) => {
        if (originalOnStop) {
          originalOnStop.call(this.mediaRecorder, event);
        }
        console.log('[WebAudioRecorder] Stop complete, URI:', this._uri);
        resolve(this._uri);
      };

      this.mediaRecorder.stop();
    });
  }

  cleanup(): void {
    if (this._uri) {
      URL.revokeObjectURL(this._uri);
      this._uri = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    this.mediaRecorder = null;
    this.audioChunks = [];
    this._isRecording = false;
    this._duration = 0;
    this.startTime = 0;
  }
}

// Export singleton instance
export const webAudioRecorder = new WebAudioRecorder();
