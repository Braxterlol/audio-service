"""
MFCCExtractor - Extrae MFCCs (Mel-Frequency Cepstral Coefficients).
"""

import numpy as np
import librosa
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
from typing import Dict
from src.audio_processing.domain.models.audio import Audio


class MFCCExtractor:
    """
    Extractor de MFCCs.
    
    Los MFCCs son características fundamentales para:
    - Reconocimiento de voz
    - Comparación de pronunciación
    - Análisis de timbre
    """
    
    def __init__(
        self,
        n_mfcc: int = 13,
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 40
    ):
        """
        Args:
            n_mfcc: Número de coeficientes MFCC a extraer
            n_fft: Tamaño de la ventana FFT
            hop_length: Número de muestras entre ventanas sucesivas
            n_mels: Número de bandas Mel
        """
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
    
    def extract(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae características MFCC del audio.
        
        Args:
            audio: Audio del cual extraer MFCCs
        
        Returns:
            Dict con:
            - mfcc_mean: Media de cada coeficiente MFCC (13 valores)
            - mfcc_std: Desviación estándar de cada coeficiente MFCC (13 valores)
            - mfcc_delta_mean: Media de deltas (derivadas)
            - mfcc_delta_std: Desviación estándar de deltas
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        
        # Extraer MFCCs
        mfccs = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels
        )
        
        # Calcular estadísticas de MFCCs
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        
        # Calcular deltas (derivadas temporales)
        mfcc_delta = librosa.feature.delta(mfccs)
        mfcc_delta_mean = np.mean(mfcc_delta, axis=1)
        mfcc_delta_std = np.std(mfcc_delta, axis=1)
        
        # Calcular delta-deltas (aceleración)
        mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
        mfcc_delta2_mean = np.mean(mfcc_delta2, axis=1)
        mfcc_delta2_std = np.std(mfcc_delta2, axis=1)
        
        # Construir diccionario de características
        features = {}
        
        # MFCCs (coeficientes 1-13)
        for i in range(self.n_mfcc):
            features[f'mfcc_{i+1}_mean'] = float(mfcc_mean[i])
            features[f'mfcc_{i+1}_std'] = float(mfcc_std[i])
        
        # Deltas
        for i in range(self.n_mfcc):
            features[f'mfcc_delta_{i+1}_mean'] = float(mfcc_delta_mean[i])
            features[f'mfcc_delta_{i+1}_std'] = float(mfcc_delta_std[i])
        
        # Delta-deltas
        for i in range(self.n_mfcc):
            features[f'mfcc_delta2_{i+1}_mean'] = float(mfcc_delta2_mean[i])
            features[f'mfcc_delta2_{i+1}_std'] = float(mfcc_delta2_std[i])
        
        # Características adicionales útiles
        features['mfcc_overall_mean'] = float(np.mean(mfcc_mean))
        features['mfcc_overall_std'] = float(np.mean(mfcc_std))
        features['mfcc_range'] = float(np.max(mfcc_mean) - np.min(mfcc_mean))
        
        return features
    
    def extract_raw_mfccs(self, audio: Audio) -> np.ndarray:
        """
        Extrae MFCCs en formato raw (matriz).
        
        Args:
            audio: Audio del cual extraer MFCCs
        
        Returns:
            np.ndarray: Matriz de MFCCs (n_mfcc x n_frames)
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        
        mfccs = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels
        )
        
        return mfccs
    
    def compare_mfccs(
        self,
        audio1: Audio,
        audio2: Audio,
        method: str = "dtw"
    ) -> float:
        """
        Compara MFCCs de dos audios.
        
        Args:
            audio1: Primer audio (usuario)
            audio2: Segundo audio (referencia)
            method: Método de comparación ("dtw", "cosine", "euclidean")
        
        Returns:
            float: Score de similitud (0-100, mayor es mejor)
        """
        mfccs1 = self.extract_raw_mfccs(audio1)
        mfccs2 = self.extract_raw_mfccs(audio2)
        
        if method == "dtw":
            # Dynamic Time Warping (mejor para comparar pronunciación)
            distance, path = fastdtw(mfccs1.T, mfccs2.T, dist=euclidean)
            
            # Normalizar distancia a score (0-100)
            # Distancias típicas: 10-50
            score = max(0, 100 - (distance[-1, -1] / len(mfccs1[0]) * 2))
            
        elif method == "cosine":
            # Similitud de coseno entre promedios
            mean1 = np.mean(mfccs1, axis=1)
            mean2 = np.mean(mfccs2, axis=1)
            
            cosine_sim = np.dot(mean1, mean2) / (
                np.linalg.norm(mean1) * np.linalg.norm(mean2)
            )
            
            # Convertir a 0-100
            score = (cosine_sim + 1) * 50  # Cosine va de -1 a 1
            
        elif method == "euclidean":
            # Distancia euclidiana entre promedios
            mean1 = np.mean(mfccs1, axis=1)
            mean2 = np.mean(mfccs2, axis=1)
            
            distance = np.linalg.norm(mean1 - mean2)
            
            # Normalizar a score (distancias típicas: 5-20)
            score = max(0, 100 - distance * 5)
            
        else:
            raise ValueError(f"Método desconocido: {method}")
        
        return float(np.clip(score, 0, 100))

