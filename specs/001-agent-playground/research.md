# Research — TCS Agent Playground

Decisiones técnicas tomadas antes de `plan.md`, con su justificación y alternativas
descartadas.

## 1. Motor de modelos: Ollama (local) vs. API en la nube

**Decisión**: Ollama, ejecutado en la máquina/servidor donde corre el backend.

**Justificación**: el argumento de negocio central del POC es la privacidad de
datos y la independencia de proveedores (ver constitución, Principios I y II).
Ollama permite ejecutar modelos open-weight (Llama 3.2, Mistral) sin enviar datos
a un tercero y sin costo variable por token — ideal para una demo interna donde
además puede no haber conectividad garantizada a internet.

**Alternativas descartadas**: API de OpenAI/Anthropic directamente — introduciría
costo por uso, dependencia de red y, sobre todo, contradiría el argumento de
privacidad que es el punto central de la propuesta a la Gerencia.

**Nota de extensibilidad**: `app/ollama_client.py` aísla toda llamada al modelo;
agregar un adaptador para un proveedor en la nube (para cargas que sí lo
justifiquen) es un cambio localizado, no una reescritura.

## 2. RAG: vectorstore dedicado vs. SQLite + cosine similarity en memoria

**Decisión**: embeddings generados con `nomic-embed-text` (vía Ollama) y
almacenados como JSON en SQLite; la búsqueda de similitud se calcula en memoria
con NumPy en el momento de la consulta.

**Justificación**: el volumen de datos de un POC (unos pocos documentos de
demostración) no justifica operar Chroma/Pinecone/pgvector. Evita dependencias
pesadas (p. ej. `onnxruntime` de Chroma) que son una fuente común de problemas
de instalación en Windows, priorizando que la demo funcione de forma confiable.

**Cuándo migrar**: si el catálogo de documentos crece a miles de fragmentos por
agente, migrar a un índice ANN (FAISS/Chroma) es un cambio contenido a `app/rag.py`.

## 3. Function calling / herramientas

**Decisión**: catálogo fijo de herramientas del lado del servidor
(`calculadora`, `fecha_actual`, `consultar_ticket_interno`), expuestas al modelo
con el formato de `tools` compatible con Ollama/OpenAI.

**Justificación**: demuestra el concepto de "conectar el agente con sistemas
internos" sin necesidad de credenciales reales de sistemas de TCS durante la
demo. `consultar_ticket_interno` simula una consulta a un Service Desk interno.

## 4. Framework de especificación: GitHub Spec Kit (metodología SDD)

**Decisión**: seguir la estructura de carpetas y documentos de
[github/spec-kit](https://github.com/github/spec-kit) (`.specify/memory/constitution.md`,
`specs/NNN-feature/{spec,plan,tasks,research,data-model,quickstart}.md`) de forma
manual, sin depender del CLI `specify` (que requiere `uv`, no preinstalado en el
entorno de desarrollo usado para este POC).

**Justificación**: se prioriza tener los artefactos de especificación correctos
y completos en el tiempo disponible; el valor de Spec Kit para este proyecto es
la disciplina de documentar *Constitución -> Especificación -> Plan -> Tareas*
antes/junto con el código, no la herramienta CLI en sí misma.

## 5. Frontend: React + Vite + Tailwind vs. low-code (Langflow/Flowise/Dify)

**Decisión**: construir una interfaz a medida en React, en vez de adoptar una
plataforma open-source existente (Langflow, Flowise, AutoGen Studio, Dify).

**Justificación**: el objetivo del POC es también demostrar una experiencia de
usuario propia, alineada a la identidad visual de TCS y al flujo mental de un
gerente no técnico — algo que las plataformas genéricas no ofrecen "out of the
box". Para una fase productiva, evaluar si conviene adoptar/forkear una de estas
plataformas en vez de mantener un frontend propio sigue siendo una opción válida
(mencionado como trabajo futuro).

## 6. RBAC simulado vs. autenticación real

**Decisión**: un selector de "usuario simulado" en el frontend, sin login real;
el backend no valida tokens de sesión.

**Justificación**: integrar SSO/Active Directory corporativo es trabajo de
integración de plataforma, no de este POC (ver "Fuera de Alcance" en `spec.md`).
Simular el rol permite demostrar el *concepto* de RBAC sin ese esfuerzo.
