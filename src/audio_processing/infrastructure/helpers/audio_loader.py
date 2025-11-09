"""
AudioLoader - Carga y decodifica audio desde diferentes formatos.
"""

import base64
import io
import tempfile
import os
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from typing import Tuple, Optional
from src.audio_processing.domain.models.audio import Audio, AudioMetadata


class AudioLoader:
    """
    Cargador de audio que maneja múltiples formatos.
    
    Soporta:
    - Base64 (desde app móvil)
    - Archivos locales
    - URLs (para audios de referencia)
    - Diferentes formatos: wav, mp3, m4a, ogg
    """
    
    def __init__(self, target_sample_rate: int = 16000):
        """
        Args:
            target_sample_rate: Frecuencia de muestreo objetivo (Hz)
        """
        self.target_sample_rate = target_sample_rate
    
    def load_from_base64(
        self,
        base64_data: str,
        source: str = "user"
    ) -> Audio:
        """
        Carga audio desde base64.
        
        Args:
            base64_data: Audio en base64, puede incluir data URI
            source: 'user' o 'reference'
        
        Returns:
            Audio: Objeto Audio con datos cargados
        
        Raises:
            ValueError: Si el formato es inválido
        """
        # Remover data URI prefix si existe
        # Ej: "data:audio/wav;base64,UklGRiQAAABXQVZF..."
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
        
        try:
            # Decodificar base64
            audio_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Error decodificando base64: {str(e)}")
        
        # Cargar desde bytes
        return self.load_from_bytes(audio_bytes, source)
    
    def load_from_bytes(
        self,
        audio_bytes: bytes,
        source: str = "user"
    ) -> Audio:
        """
        Carga audio desde bytes.
        
        Args:
            audio_bytes: Audio como bytes
            source: 'user' o 'reference'
        
        Returns:
            Audio: Objeto Audio
        """
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Intentar cargar con librosa directamente
            try:
                y, sr = librosa.load(tmp_path, sr=self.target_sample_rate, mono=True)
                duration = librosa.get_duration(y=y, sr=sr)
                
                metadata = AudioMetadata(
                    sample_rate=sr,
                    duration_seconds=float(duration),
                    channels=1,
                    format="wav"
                )
                
                return Audio(data=y, metadata=metadata, source=source)
            
            except Exception as librosa_error:
                # Si librosa falla, intentar con pydub (soporta más formatos)
                audio_segment = AudioSegment.from_file(tmp_path)
                
                # Convertir a mono y resample
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                
                audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
                
                # Convertir a numpy array
                samples = np.array(audio_segment.get_array_of_samples())
                
                # Normalizar a float32 [-1, 1]
                if audio_segment.sample_width == 2:  # 16-bit
                    y = samples.astype(np.float32) / 32768.0
                elif audio_segment.sample_width == 4:  # 32-bit
                    y = samples.astype(np.float32) / 2147483648.0
                else:
                    y = samples.astype(np.float32)
                
                duration = len(y) / self.target_sample_rate
                
                metadata = AudioMetadata(
                    sample_rate=self.target_sample_rate,
                    duration_seconds=float(duration),
                    channels=1,
                    format="unknown"
                )
                
                return Audio(data=y, metadata=metadata, source=source)
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def load_from_file(
        self,
        file_path: str,
        source: str = "reference"
    ) -> Audio:
        """
        Carga audio desde archivo local o URL.
        
        Args:
            file_path: Path del archivo o URL
            source: 'user' o 'reference'
        
        Returns:
            Audio: Objeto Audio
        """
        try:
            y, sr = librosa.load(
                file_path,
                sr=self.target_sample_rate,
                mono=True
            )
            
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Determinar formato del archivo
            file_format = os.path.splitext(file_path)[1].replace('.', '').lower()
            
            metadata = AudioMetadata(
                sample_rate=sr,
                duration_seconds=float(duration),
                channels=1,
                format=file_format or "wav"
            )
            
            return Audio(data=y, metadata=metadata, source=source)
        
        except Exception as e:
            raise ValueError(f"Error cargando audio desde {file_path}: {str(e)}")
    
    def save_to_file(
        self,
        audio: Audio,
        output_path: str,
        format: str = "wav"
    ):
        """
        Guarda audio a archivo.
        
        Args:
            audio: Objeto Audio
            output_path: Path de salida
            format: Formato de salida (wav, mp3, etc.)
        """
        sf.write(
            output_path,
            audio.data,
            audio.metadata.sample_rate,
            format=format
        )
    
    def audio_to_base64(self, audio: Audio) -> str:
        """
        Convierte Audio a base64 (útil para testing).
        
        Args:
            audio: Objeto Audio
        
        Returns:
            str: Audio en base64
        """
        # Guardar a buffer temporal
        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio.data,
            audio.metadata.sample_rate,
            format='WAV'
        )
        buffer.seek(0)
        
        # Convertir a base64
        audio_bytes = buffer.read()
        base64_str = base64.b64encode(audio_bytes).decode('utf-8')
        
        return f"data:audio/wav;base64,{base64_str}"
