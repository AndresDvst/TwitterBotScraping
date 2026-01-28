"""
Sistema de checkpoints para recuperación de estado
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from logger import bot_logger
from config import Config


class CheckpointManager:
    """Gestiona checkpoints para recuperación de estado"""
    
    def __init__(self, checkpoint_dir: str = None):
        self.checkpoint_dir = checkpoint_dir or os.path.join(Config.DATA_DIR, 'checkpoints')
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, 'latest_checkpoint.json')
    
    def save_checkpoint(self, state: Dict[str, Any]) -> bool:
        """
        Guarda un checkpoint del estado actual
        
        Args:
            state: Diccionario con el estado a guardar
            
        Returns:
            True si se guardó correctamente
        """
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'state': state
            }
            
            # Escritura atómica (temp + rename)
            temp_file = self.checkpoint_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            # Renombrar (operación atómica en la mayoría de sistemas)
            os.replace(temp_file, self.checkpoint_file)
            
            bot_logger.debug(f"Checkpoint guardado: {checkpoint_data['timestamp']}")
            return True
            
        except Exception as e:
            bot_logger.error(f"Error guardando checkpoint: {e}")
            return False
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Carga el último checkpoint guardado
        
        Returns:
            Diccionario con el estado o None si no existe
        """
        try:
            if not os.path.exists(self.checkpoint_file):
                bot_logger.debug("No se encontró checkpoint previo")
                return None
            
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            bot_logger.info(f"Checkpoint cargado desde: {checkpoint_data['timestamp']}")
            return checkpoint_data['state']
            
        except Exception as e:
            bot_logger.error(f"Error cargando checkpoint: {e}")
            return None
    
    def clear_checkpoint(self) -> bool:
        """
        Elimina el checkpoint actual
        
        Returns:
            True si se eliminó correctamente
        """
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                bot_logger.info("Checkpoint eliminado")
            return True
        except Exception as e:
            bot_logger.error(f"Error eliminando checkpoint: {e}")
            return False
    
    def get_checkpoint_age(self) -> Optional[float]:
        """
        Retorna la edad del checkpoint en segundos
        
        Returns:
            Segundos desde el último checkpoint o None
        """
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return None
        
        try:
            checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
            age = (datetime.now() - checkpoint_time).total_seconds()
            return age
        except:
            return None
