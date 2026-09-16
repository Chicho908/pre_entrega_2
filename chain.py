# logging deja registro de cada paso: cuando arranca el procesamiento,
# si se valido bien, o si fallo despues de los reintentos.
import logging

# load_dotenv lee el .env y carga la API key como variable de entorno.
from dotenv import load_dotenv

# ChatAnthropic es el mismo proveedor que ya usamos y probamos en el Modulo 1.
from langchain_anthropic import ChatAnthropic

# ChatPromptTemplate evita hardcodear f-strings: LangChain resuelve {texto} solo.
from langchain_core.prompts import ChatPromptTemplate

# Runnable es el tipo de retorno de una cadena LCEL (prompt | modelo | ...).
from langchain_core.runnables import Runnable

from schemas import EntidadesTecnicas

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Prompt modular con roles separados: la instruccion del sistema (el rol del
# analista) queda aparte del mensaje humano (el texto a procesar).
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Sos un analista tecnico. Analiza el texto que te pasa el usuario y extrae: "
     "las tecnologias, frameworks o herramientas mencionadas, el nivel de "
     "criticidad del problema o arquitectura descripta, y un resumen tecnico breve."),
    ("human", "{texto}"),
])


def build_chain() -> Runnable:
    # temperature=0 porque para extraccion estructurada queremos determinismo,
    # no creatividad. No tiene sentido "inventar" tecnologias que no estan en el texto.
    # max_tokens con margen para que la respuesta (JSON + resumen) no se corte
    # a mitad de camino: una respuesta cortada es un objeto incompleto, que es
    # justo el error que with_retry tiene que poder reintentar.
    model = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0, max_tokens=1024)

    # with_structured_output fuerza al modelo a devolver directamente una
    # instancia de EntidadesTecnicas (ya validada), no texto plano. Al usar
    # tool calling, si la respuesta viene incompleta o mal formada Pydantic
    # la rechaza sola con un error, sin que tengamos que revisar a mano el
    # finish_reason de la respuesta cruda.
    structured_model = model.with_structured_output(EntidadesTecnicas)

    # with_retry: si el LLM devuelve un JSON mal formado o incompleto (por
    # ejemplo cortado por limite de tokens), reintenta antes de fallar del todo.
    chain = (prompt | structured_model).with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )
    return chain


# Funcion asincrona que ejecuta la cadena con .ainvoke() (no bloqueante) y
# deja logs del proceso, incluyendo el error final si fallan todos los reintentos.
async def process_text(text: str) -> EntidadesTecnicas:
    chain = build_chain()
    logger.info("Procesando texto (%d caracteres)...", len(text))

    try:
        resultado = await chain.ainvoke({"texto": text})
        logger.info("Extraccion validada: %s", resultado.model_dump())
        return resultado
    except Exception as e:
        # Si with_retry ya agoto los 3 intentos, esto es el fallo definitivo.
        logger.error("Fallo tras los reintentos: %s", e)
        raise
