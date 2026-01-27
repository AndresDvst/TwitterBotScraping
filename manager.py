import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set

class UsuariosManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.usuarios_base_path = os.path.join(data_dir, "usuarios_base.json")
        self.historial_path = os.path.join(data_dir, "historial_entregados.json")
        self.repetidos_path = os.path.join(data_dir, "usuarios_repetidos.json")
        self.principales_path = os.path.join(data_dir, "usuarios_principales.json")
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Inicializar archivos
        self._inicializar_archivos()
    
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
    
    def _cargar_json(self, path: str) -> List:
        """Carga un archivo JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _guardar_json(self, path: str, data: List):
        """Guarda datos en un archivo JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def cargar_usuarios_base(self) -> List[str]:
        """Carga usuarios base y los migra a principales si está vacío"""
        base = self._cargar_json(self.usuarios_base_path)
        principales = self._cargar_json(self.principales_path)
        
        # Si principales está vacío, copiar desde base
        if not principales and base:
            self._guardar_json(self.principales_path, base)
            principales = base.copy()
        
        return principales
    
    def obtener_10_usuarios(self) -> List[str]:
        """Obtiene 10 usuarios aleatorios que no se hayan entregado en los últimos 3 días"""
        principales = self._cargar_json(self.principales_path)
        historial = self._cargar_json(self.historial_path)
        
        # Filtrar usuarios entregados en los últimos 3 días
        fecha_limite = datetime.now() - timedelta(days=3)
        usuarios_bloqueados = set()
        
        for entry in historial:
            fecha_entrega = datetime.fromisoformat(entry['fecha'])
            if fecha_entrega > fecha_limite:
                usuarios_bloqueados.add(entry['usuario'])
        
        # Usuarios disponibles
        usuarios_disponibles = [u for u in principales if u not in usuarios_bloqueados]
        
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
        
        return seleccionados
    
    def agregar_nuevos_usuarios(self, nuevos_usuarios: List[str]):
        """Agrega nuevos usuarios verificando duplicados"""
        principales = set(self._cargar_json(self.principales_path))
        repetidos = self._cargar_json(self.repetidos_path)
        
        usuarios_agregados = []
        
        for usuario in nuevos_usuarios:
            # Limpiar username
            usuario_limpio = usuario.strip().replace('@', '')
            
            if usuario_limpio and usuario_limpio not in principales:
                principales.add(usuario_limpio)
                usuarios_agregados.append(usuario_limpio)
            elif usuario_limpio in principales:
                # Registrar repetido con timestamp
                repetidos.append({
                    'usuario': usuario_limpio,
                    'fecha': datetime.now().isoformat()
                })
        
        # Guardar cambios
        self._guardar_json(self.principales_path, list(principales))
        self._guardar_json(self.repetidos_path, repetidos)
        
        return usuarios_agregados
    
    def limpiar_historial_antiguo(self, dias=30):
        """Limpia entradas del historial más antiguas que X días"""
        historial = self._cargar_json(self.historial_path)
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        historial_limpio = [
            entry for entry in historial 
            if datetime.fromisoformat(entry['fecha']) > fecha_limite
        ]
        
        self._guardar_json(self.historial_path, historial_limpio)
        return len(historial) - len(historial_limpio)
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del sistema"""
        return {
            'total_principales': len(self._cargar_json(self.principales_path)),
            'total_historial': len(self._cargar_json(self.historial_path)),
            'total_repetidos': len(self._cargar_json(self.repetidos_path)),
            'total_base': len(self._cargar_json(self.usuarios_base_path))
        }
    
    def modificar_login_json(self, usuarios_fuente: List[str], destino: str, nombres: List[str] = None, total_usuarios: int = 40) -> Dict:
        if nombres is None:
            nombres = ["aurora", "emily", "eva", "gaby"]
        import random, json
        usuarios_fuente = [u.strip().replace('@', '') for u in usuarios_fuente if u and u.strip()]
        seleccion_total = random.sample(usuarios_fuente, min(total_usuarios, len(usuarios_fuente)))
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
            lines.append(f'    }}{"," if j < 4 else ""}')
        lines.append("  }")
        lines.append("}")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return estructura
