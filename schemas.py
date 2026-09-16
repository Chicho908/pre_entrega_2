# Enum hace que nivel_de_criticidad sea una lista cerrada de opciones validas,
# asi el modelo no puede inventar un valor como "high" o "ALTA".
from enum import Enum

# List tipa la lista de tecnologias que devuelve el LLM.
from typing import List

# Pydantic valida y documenta la estructura de datos que exigimos como salida.
from pydantic import BaseModel, Field, field_validator


# Nivel de criticidad como enum: solo estos 3 valores son validos.
class NivelCriticidad(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


# Este es el contrato de datos: lo que el LLM tiene que devolver si o si,
# ya validado, para que el resto del programa pueda confiar en su forma.
class EntidadesTecnicas(BaseModel):
    # min_length=1 evita aceptar una lista vacia (sin tecnologias detectadas).
    tecnologias: List[str] = Field(
        ..., min_length=1,
        description="Tecnologias, frameworks o herramientas mencionadas en el texto"
    )
    nivel_de_criticidad: NivelCriticidad = Field(
        ..., description="Gravedad del problema o relevancia de la arquitectura descripta"
    )
    # min_length=10 evita un resumen vacio o de una sola palabra.
    resumen_tecnico: str = Field(
        ..., min_length=10,
        description="Resumen tecnico de 1-2 oraciones sobre el contenido del texto"
    )

    # Validacion semantica extra que el tipado solo no cubre: limpio espacios
    # y saco duplicados (dict.fromkeys mantiene el orden, a diferencia de un set).
    # Si despues de limpiar no queda nada, corto con un error.
    @field_validator("tecnologias")
    @classmethod
    def sin_duplicados_ni_vacios(cls, v: List[str]) -> List[str]:
        limpio = [t.strip() for t in v if t.strip()]
        if not limpio:
            raise ValueError("La lista de tecnologias no puede quedar vacia")
        return list(dict.fromkeys(limpio))
