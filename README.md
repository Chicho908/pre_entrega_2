# Pre-entrega 2: Pipeline de procesamiento validado

Pipeline de extraccion de entidades tecnicas (Modulo 2, CoderHouse - Desarrollo de
aplicaciones con LLMs). Recibe un texto libre (un log de error o una descripcion
de arquitectura de software) y devuelve un objeto validado con Pydantic: las
tecnologias mencionadas, el nivel de criticidad y un resumen tecnico.

## Que hace

1. **`schemas.py`** — define `EntidadesTecnicas`, el contrato de datos con Pydantic:
   `tecnologias` (lista, no puede quedar vacia ni con duplicados), `nivel_de_criticidad`
   (enum cerrado: `baja` / `media` / `alta`) y `resumen_tecnico` (string).
2. **`chain.py`** — arma la cadena LCEL: un `ChatPromptTemplate` modular (roles
   `system`/`human`) unido a `ChatAnthropic.with_structured_output(EntidadesTecnicas)`,
   envuelta en `.with_retry()` para reintentar automaticamente si el LLM devuelve
   una respuesta mal formada o incompleta. Expone `process_text(text: str)`, una
   funcion asincrona que ejecuta la cadena con `.ainvoke()` y deja logs de cada paso.
3. **`main.py`** — mini-script de prueba: corre el pipeline con un texto
   de ejemplo con tecnologias claras, y con un texto ambiguo (prueba de estres)
   para ver como se comporta el validador cuando no hay informacion tecnica clara.

## Como correrlo

```bash
python -m venv venv
venv\\Scripts\\activate        # en Windows
# source venv/bin/activate    # en Linux/Mac
pip install -r requirements.txt
copy .env.example .env        # completar con tu ANTHROPIC_API_KEY real
python main.py
```

## Estructura del repositorio

```
.
├── schemas.py          # modelo Pydantic: el contrato de datos (EntidadesTecnicas)
├── chain.py             # cadena LCEL (prompt | model.with_structured_output) + retry + process_text async
├── main.py      # mini-script de prueba asincrono
├── requirements.txt      # dependencias con versiones fijadas
├── .env.example          # plantilla de variables de entorno (sin la key real)
└── .gitignore            # excluye .env, venv/ y __pycache__/
```

## Ejemplo de salida esperada

Con el texto de ejemplo de `main.py` (API en FastAPI con timeouts, cache
en Redis saturado, pool de conexiones a PostgreSQL agotado), el pipeline devuelve:

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con cache en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```

## Decisiones de diseno

- **`ChatAnthropic` en vez de `ChatOpenAI`**: la consigna permite cualquiera de los
  dos ("reutilizando la logica del Modulo 1"); se eligio Anthropic porque ya esta
  la API key probada en vivo desde la Pre-entrega 1 y el ejercicio del Modulo 2.
- **`with_structured_output` en vez de `PydanticOutputParser`**: la consigna
  menciona ambas opciones pero marca `with_structured_output` como la preferida
  para OpenAI/Anthropic. Al forzar el schema por tool calling, si la respuesta del
  modelo viene incompleta o mal formada, Pydantic la rechaza sola con una excepcion
  clara — no hace falta revisar el `finish_reason` de la respuesta cruda a mano,
  que es el error mas comun que la consigna pide evitar.
- **`temperature=0`**: para extraccion estructurada se busca que el modelo sea
  determinista (mismo texto, misma respuesta), no creativo.
- **`max_tokens=1024` explicito**: le da margen a la respuesta (el JSON de la
  herramienta mas el resumen tecnico) para no cortarse a mitad de camino. Una
  respuesta cortada por limite de tokens es un objeto incompleto — justo el caso
  que `.with_retry()` esta pensado para reintentar.
- **`.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)`**: reintenta
  hasta 3 veces con espera exponencial y jitter (aleatoriedad) entre intentos, para
  no reintentar todos al mismo tiempo si hay un problema temporal de la API.
- **Sin f-strings hardcodeadas en el prompt**: se uso `ChatPromptTemplate` con la
  variable `{texto}`, para que LangChain gestione la entrada en vez de armar el
  mensaje a mano.
- **Versiones fijadas en `requirements.txt`** (`langchain==1.4.1`,
  `langchain-anthropic==1.7.2`, `python-dotenv==1.2.3`): son las versiones ya
  probadas y funcionando en este entorno, para garantizar reproducibilidad exacta
  si alguien clona el repo mas adelante.
- **`.env` fuera del repo**: la API key real nunca se sube (esta en `.gitignore`);
  solo se versiona `.env.example` como plantilla.
