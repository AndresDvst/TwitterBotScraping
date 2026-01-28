"""
Gestor de usuarios con logging, backups y validación mejorada
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set
from logger import bot_logger, log_exception
from backup import BackupManager
from config import Config


class UsuariosManager:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or Config.DATA_DIR
        self.usuarios_base_path = os.path.join(self.data_dir, "usuarios_base.json")
        self.historial_path = os.path.join(self.data_dir, "historial_entregados.json")
        self.repetidos_path = os.path.join(self.data_dir, "usuarios_repetidos.json")
        self.principales_path = os.path.join(self.data_dir, "usuarios_principales.json")
        
        # Inicializar backup manager
        self.backup_manager = BackupManager()
        
        # Crear directorio si no existe
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inicializar archivos
        self._inicializar_archivos()
        
        bot_logger.info(f"UsuariosManager inicializado con data_dir: {self.data_dir}")
    
    def _inicializar_archivos(self):
        """Crea los archivos JSON si no existen"""
        archivos = {
            self.usuarios_base_path: [],
            self.historial_path: [],
            self.repetidos_path: [],
            self.principales_path: []
        }
        
        for path, default in archivos.items():
            if not os.path.exists(path):
                self._guardar_json(path, default)
                bot_logger.debug(f"Archivo inicializado: {os.path.basename(path)}")
    
    def _cargar_json(self, path: str) -> List:
        """Carga un archivo JSON con manejo de errores"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bot_logger.debug(f"Archivo cargado: {os.path.basename(path)} ({len(data)} items)")
            return data
        except FileNotFoundError:
            bot_logger.warning(f"Archivo no encontrado: {path}")
            return []
        except json.JSONDecodeError as e:
            bot_logger.error(f"Error decodificando JSON en {path}: {e}")
            return []
        except Exception as e:
            log_exception(bot_logger, e, f"Error cargando {path}")
            return []
    
    def _guardar_json(self, path: str, data: List):
        """Guarda datos en un archivo JSON con backup automático"""
        try:
            # Crear backup antes de modificar
            if os.path.exists(path):
                self.backup_manager.create_backup(path)
            
            # Escritura atómica (temp + rename)
            temp_path = path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_path, path)
            bot_logger.debug(f"Archivo guardado: {os.path.basename(path)} ({len(data)} items)")
            
        except Exception as e:
            log_exception(bot_logger, e, f"Error guardando {path}")
            raise
    
    def cargar_usuarios_base(self) -> List[str]:
        """Carga usuarios base y los migra a principales si está vacío"""
        base = self._cargar_json(self.usuarios_base_path)
        principales = self._cargar_json(self.principales_path)
        
        # Si principales está vacío, copiar desde base
        if not principales and base:
            self._guardar_json(self.principales_path, base)
            principales = base.copy()
            bot_logger.info(f"Migrados {len(base)} usuarios de base a principales")
        
        return principales
    
    def obtener_10_usuarios(self) -> List[str]:
        """Obtiene 10 usuarios aleatorios que no se hayan entregado en los últimos 3 días"""
        principales = self._cargar_json(self.principales_path)
        historial = self._cargar_json(self.historial_path)
        
        # Filtrar usuarios entregados en los últimos 3 días
        fecha_limite = datetime.now() - timedelta(days=3)
        usuarios_bloqueados = set()
        
        for entry in historial:
            try:
                fecha_entrega = datetime.fromisoformat(entry['fecha'])
                if fecha_entrega > fecha_limite:
                    usuarios_bloqueados.add(entry['usuario'])
            except (KeyError, ValueError) as e:
                bot_logger.warning(f"Entrada inválida en historial: {entry}")
                continue
        
        # Usuarios disponibles
        usuarios_disponibles = [u for u in principales if u not in usuarios_bloqueados]
        
        bot_logger.info(
            f"Usuarios disponibles: {len(usuarios_disponibles)}/{len(principales)} "
            f"(bloqueados últimos 3 días: {len(usuarios_bloqueados)})"
        )
        
        # Si no hay suficientes, retornar los que haya
        import random
        cantidad = min(10, len(usuarios_disponibles))
        seleccionados = random.sample(usuarios_disponibles, cantidad) if cantidad > 0 else []
        
        # Registrar en historial
        for usuario in seleccionados:
            historial.append({
                'usuario': usuario,
                'fecha': datetime.now().isoformat()
            })
        
        self._guardar_json(self.historial_path, historial)
        
        bot_logger.info(f"Seleccionados {len(seleccionados)} usuarios")
        return seleccionados
    
    def agregar_nuevos_usuarios(self, nuevos_usuarios: List[str]) -> List[str]:
        """Agrega nuevos usuarios verificando duplicados"""
        principales = set(self._cargar_json(self.principales_path))
        repetidos = self._cargar_json(self.repetidos_path)
        
        usuarios_agregados = []
        usuarios_repetidos_count = 0
        
        for usuario in nuevos_usuarios:
            # Limpiar username
            usuario_limpio = usuario.strip().replace('@', '')
            
            if not usuario_limpio:
                continue
            
            if usuario_limpio not in principales:
                principales.add(usuario_limpio)
                usuarios_agregados.append(usuario_limpio)
            else:
                usuarios_repetidos_count += 1
                # Registrar repetido con timestamp
                repetidos.append({
                    'usuario': usuario_limpio,
                    'fecha': datetime.now().isoformat()
                })
        
        # Guardar cambios
        self._guardar_json(self.principales_path, list(principales))
        self._guardar_json(self.repetidos_path, repetidos)
        
        bot_logger.info(
            f"Procesados {len(nuevos_usuarios)} usuarios: "
            f"{len(usuarios_agregados)} nuevos, {usuarios_repetidos_count} repetidos"
        )
        
        return usuarios_agregados
    
    def limpiar_historial_antiguo(self, dias: int = None) -> int:
        """Limpia entradas del historial más antiguas que X días"""
        dias = dias or Config.DIAS_HISTORIAL_LIMPIEZA
        historial = self._cargar_json(self.historial_path)
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        historial_limpio = []
        for entry in historial:
            try:
                if datetime.fromisoformat(entry['fecha']) > fecha_limite:
                    historial_limpio.append(entry)
            except (KeyError, ValueError):
                continue
        
        eliminados = len(historial) - len(historial_limpio)
        
        if eliminados > 0:
            self._guardar_json(self.historial_path, historial_limpio)
            bot_logger.info(f"Limpiados {eliminados} registros del historial (>{dias} días)")
        else:
            bot_logger.info(f"No hay registros antiguos para limpiar (>{dias} días)")
        
        return eliminados
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del sistema"""
        stats = {
            'total_principales': len(self._cargar_json(self.principales_path)),
            'total_historial': len(self._cargar_json(self.historial_path)),
            'total_repetidos': len(self._cargar_json(self.repetidos_path)),
            'total_base': len(self._cargar_json(self.usuarios_base_path))
        }
        
        bot_logger.debug(f"Estadísticas: {stats}")
        return stats
    
    def modificar_login_json(
        self, 
        usuarios_fuente: List[str], 
        destino: str = None, 
        nombres: List[str] = None, 
        total_usuarios: int = 40
    ) -> Dict:
        """Modifica login.json con usuarios aleatorios distribuidos"""
        destino = destino or Config.LOGIN_JSON_PATH
        
        if nombres is None:
            nombres = ["aurora", "emily", "eva", "gaby"]
        
        import random
        
        try:
            usuarios_fuente = list({u.strip().replace('@', '') for u in usuarios_fuente if u and u.strip()})
            
            if len(usuarios_fuente) < total_usuarios:
                raise ValueError(f"Se requieren al menos {total_usuarios} usuarios únicos para generar login.json")
            
            seleccion_total = random.sample(usuarios_fuente, total_usuarios)
            por_grupo = max(1, len(seleccion_total) // len(nombres))
            estructura = {"keywords": {}}
            idx = 0
            
            for i, nombre in enumerate(nombres, start=1):
                grupo = seleccion_total[idx: idx + por_grupo]
                idx += por_grupo
                estructura["keywords"][str(i)] = {
                    "name": nombre,
                    "keywords": grupo
                }
            
            # Si quedaron usuarios sin asignar, distribuirlos
            restantes = seleccion_total[idx:]
            if restantes:
                for r in restantes:
                    clave = str(random.randint(1, len(nombres)))
                    estructura["keywords"][clave]["keywords"].append(r)
            
            # Escribir formato lateral
            lines = ["{", '  "keywords": {']
            for j, clave in enumerate(["1", "2", "3", "4"], start=1):
                entry = estructura["keywords"][clave]
                name_txt = json.dumps(entry["name"], ensure_ascii=False)
                kws_inline = "[" + ",".join(json.dumps(x, ensure_ascii=False) for x in entry["keywords"]) + "]"
                lines.append(f'    "{clave}": {{')
                lines.append(f'      "name": {name_txt},')
                lines.append(f'      "keywords": {kws_inline}')
                lines.append(f'    }}{","if j < 4 else ""}')
            lines.append("  }")
            lines.append("}")
            
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            bot_logger.info(f"login.json actualizado en: {destino} ({total_usuarios} usuarios)")
            return estructura
            
        except Exception as e:
            log_exception(bot_logger, e, "Error modificando login.json")
            raise

