# Production Incident Analyzer
## Traditional Prompt Engineering vs. DSPy

### 1. Introducción

Estamos desarrollando un **analizador de incidentes de producción basado en Large Language Models (LLMs)**.

El sistema recibe información técnica, como logs de aplicación, contexto del sistema, despliegues recientes e incidentes históricos, junto con el impacto de negocio y las políticas de severidad.

A partir de esta información, genera un análisis estructurado que incluye:

- **Clasificación del incidente:** identifica el tipo de problema, como Database, Application o Network.
- **Severidad:** determina la gravedad del incidente (Critical, High, Medium o Low) de acuerdo con las políticas definidas.
- **Posible causa raíz:** propone una hipótesis sobre el origen del problema.
- **Evidencias:** identifica la información que respalda el diagnóstico y aquella que todavía falta para confirmarlo.
- **Acciones correctivas:** recomienda posibles pasos para investigar y resolver el incidente.
- **Nivel de confianza:** estima qué tan respaldada está la hipótesis de causa raíz por la evidencia disponible.

### 2. Objetivo del proyecto

El objetivo principal es **comparar dos enfoques para desarrollar aplicaciones basadas en LLMs**:

**Traditional Prompt Engineering**

Las instrucciones que recibe el modelo se diseñan, escriben y modifican manualmente. Para mejorar los resultados, se ajustan las reglas, el contexto y los ejemplos incluidos en el prompt.

**DSPy (Declarative Self-improving Python)**

El comportamiento esperado se define mediante `Signatures` y `Modules`. Además, DSPy proporciona optimizadores que permiten ajustar los programas utilizando ejemplos de entrenamiento y métricas de evaluación.

La comparación busca determinar cómo influyen ambos enfoques en:

- **Calidad de las respuestas:** precisión de las clasificaciones y calidad del análisis generado.
- **Consumo de tokens:** cantidad de tokens procesados por el modelo.
- **Latencia:** tiempo necesario para generar una respuesta.
- **Costo monetario:** costo asociado a las llamadas al LLM.
- **Mantenimiento:** facilidad para modificar y mejorar el comportamiento del sistema.

### 3. Alcance inicial

Para realizar el experimento utilizamos el modelo `gpt-4.1-mini` y un conjunto de incidentes ficticios pero representativos de problemas que pueden ocurrir en aplicaciones de producción.

Se implementaron cuatro configuraciones:

1. Traditional Prompt Engineering — versión inicial.
2. Traditional Prompt Engineering — versión modificada manualmente.
3. DSPy — implementación baseline con `Predict`.
4. DSPy — implementación optimizada con `BootstrapFewShot`.

Todas las configuraciones se evalúan utilizando el mismo conjunto de incidentes.

En la primera etapa, la métrica principal de calidad es la **precisión en la clasificación de severidad (Accuracy)**.

Aunque el analizador genera otros campos, como la causa raíz y el nivel de confianza, estos todavía no forman parte de la evaluación automática de calidad.

El propósito del proyecto no es demostrar que un enfoque siempre supera al otro, sino **analizar sus diferencias mediante resultados medibles y reproducibles**.