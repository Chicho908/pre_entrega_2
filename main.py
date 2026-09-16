# Mini-script de prueba: ejecuta el pipeline con un texto de ejemplo y,
# como sugiere la consigna, tambien con un texto ambiguo para ver como
# se comporta el modelo cuando no hay tecnologias claras mencionadas.
import asyncio

from chain import process_text

texto_ejemplo = (
    "Nuestra API en FastAPI esta devolviendo timeouts intermitentes. El cache en "
    "Redis parece saturarse en picos de trafico y las conexiones a PostgreSQL se "
    "agotan porque el pool esta mal dimensionado. Esto esta afectando a usuarios "
    "en produccion."
)

texto_ambiguo = "El sistema anda medio raro ultimamente, no se bien que esta pasando."


async def main():
    print("--- Texto con tecnologias claras ---")
    resultado = await process_text(texto_ejemplo)
    print(resultado.model_dump_json(indent=2))

    print("\n--- Prueba de estres: texto ambiguo ---")
    try:
        resultado_ambiguo = await process_text(texto_ambiguo)
        print(resultado_ambiguo.model_dump_json(indent=2))
    except Exception as e:
        # Si el validador de Pydantic rechaza la respuesta (ej. lista de
        # tecnologias vacia), la excepcion llega hasta aca.
        print(f"El pipeline no pudo validar una respuesta: {e}")


if __name__ == "__main__":
    asyncio.run(main())
