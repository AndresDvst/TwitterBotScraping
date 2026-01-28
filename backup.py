"""
Sistema de backups automáticos para archivos JSON
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List
from logger import bot_logger
from config import Config


class BackupManager:
    """Gestiona backups automáticos de archivos de datos"""
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = backup_dir or Config.BACKUP_DIR
        self.enabled = Config.BACKUP_ENABLED
        
        if self.enabled:
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, file_path: str) -> bool:
        """
        Crea un backup de un archivo
        
        Args:
            file_path: Ruta del archivo a respaldar
            
        Returns:
            True si se creó el backup correctamente
        """
        if not self.enabled:
            return False
        
        try:
            if not os.path.exists(file_path):
                bot_logger.warning(f"Archivo no existe para backup: {file_path}")
                return False
            
            # Nombre del backup con timestamp
            filename = Path(file_path).name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filename}.{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copiar archivo
            shutil.copy2(file_path, backup_path)
            
            bot_logger.debug(f"Backup creado: {backup_name}")
            
            # Limpiar backups antiguos
            self._cleanup_old_backups(filename)
            
            return True
            
        except Exception as e:
            bot_logger.error(f"Error creando backup de {file_path}: {e}")
            return False
    
    def _cleanup_old_backups(self, filename: str):
        """
        Elimina backups antiguos manteniendo solo los últimos N
        
        Args:
            filename: Nombre base del archivo
        """
        try:
            # Buscar todos los backups de este archivo
            pattern = f"{filename}.*.bak"
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.startswith(filename) and file.endswith('.bak'):
                    backup_path = os.path.join(self.backup_dir, file)
                    backups.append((backup_path, os.path.getmtime(backup_path)))
            
            # Ordenar por fecha (más reciente primero)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Eliminar los más antiguos
            if len(backups) > Config.MAX_BACKUPS:
                for backup_path, _ in backups[Config.MAX_BACKUPS:]:
                    os.remove(backup_path)
                    bot_logger.debug(f"Backup antiguo eliminado: {Path(backup_path).name}")
                    
        except Exception as e:
            bot_logger.error(f"Error limpiando backups antiguos: {e}")
    
    def restore_backup(self, file_path: str, backup_name: str = None) -> bool:
        """
        Restaura un archivo desde un backup
        
        Args:
            file_path: Ruta del archivo a restaurar
            backup_name: Nombre específico del backup (o None para el más reciente)
            
        Returns:
            True si se restauró correctamente
        """
        try:
            filename = Path(file_path).name
            
            if backup_name:
                backup_path = os.path.join(self.backup_dir, backup_name)
            else:
                # Buscar el backup más reciente
                backups = []
                for file in os.listdir(self.backup_dir):
                    if file.startswith(filename) and file.endswith('.bak'):
                        backup_path_temp = os.path.join(self.backup_dir, file)
                        backups.append((backup_path_temp, os.path.getmtime(backup_path_temp)))
                
                if not backups:
                    bot_logger.warning(f"No se encontraron backups para {filename}")
                    return False
                
                # Ordenar y tomar el más reciente
                backups.sort(key=lambda x: x[1], reverse=True)
                backup_path = backups[0][0]
            
            if not os.path.exists(backup_path):
                bot_logger.error(f"Backup no encontrado: {backup_path}")
                return False
            
            # Restaurar
            shutil.copy2(backup_path, file_path)
            bot_logger.info(f"Archivo restaurado desde: {Path(backup_path).name}")
            
            return True
            
        except Exception as e:
            bot_logger.error(f"Error restaurando backup: {e}")
            return False
    
    def list_backups(self, filename: str = None) -> List[str]:
        """
        Lista todos los backups disponibles
        
        Args:
            filename: Filtrar por nombre de archivo específico
            
        Returns:
            Lista de nombres de backups
        """
        try:
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.endswith('.bak'):
                    if filename is None or file.startswith(filename):
                        backups.append(file)
            
            return sorted(backups, reverse=True)
            
        except Exception as e:
            bot_logger.error(f"Error listando backups: {e}")
            return []
