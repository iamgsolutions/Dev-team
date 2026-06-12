"""Team roles (S7) - phase task generators for the sequential pipeline.

M4 v1 design (deliberate): each phase runs ONE well-instructed macro-task.
Fine-grained task decomposition (PM plan -> N tasks) is iteration 2 - building
levels honestly instead of faking granularity (build/03 'fasificación realista').

Each role returns the kwargs for executor.execute_task(). Role-specific rules
complement the universal ones (build/05-agent-rules.md).
"""
from __future__ import annotations

from dataclasses import dataclass

from .state import Project


@dataclass
class PhaseTask:
    role: str
    task: str
    acceptance_criteria: list[str]
    expected_output: str
    critical: bool = False
    gates: list[str] | None = None
    forbidden: list[str] | None = None


def pm_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="pm",
        task=(
            "Como Product Manager: lee ./BRIEF.md y produce el PRD del proyecto en ./docs/PRD.md "
            "(crea la carpeta docs/ si no existe). El PRD debe contener: objetivo, usuarios, "
            "historias de usuario con prioridad MoSCoW, criterios de aceptación verificables por "
            "funcionalidad, alcance excluido, y un plan de fases técnico de alto nivel. "
            "NO inventes requisitos: lo que no esté en el brief y sea crítico, lístalo en una "
            "sección final 'Preguntas al humano'. Documentación en español."
        ),
        acceptance_criteria=[
            "existe ./docs/PRD.md con todas las secciones pedidas",
            "cada funcionalidad M tiene criterios de aceptación verificables",
            "las dudas críticas están en 'Preguntas al humano' (no asumidas)",
        ],
        expected_output="./docs/PRD.md",
        critical=True,  # design quality drives everything downstream
    )


def architect_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="architect",
        task=(
            "Como Architect: lee ./docs/PRD.md y decide la arquitectura con best practices. "
            "Produce: ./docs/architecture.md (stack elegido y por qué, estructura de carpetas, "
            "decisiones tipo ADR), ./docs/api-contract.md (TODOS los endpoints: ruta, método, "
            "request/response JSON, códigos de error) y ./docs/data-model.md (entidades, campos, "
            "relaciones, migración inicial). Stack por defecto del equipo: backend Python/FastAPI "
            "o Node/TypeScript (elige el que mejor encaje y justifica), frontend Next.js+React+TS, "
            "base de datos Postgres. Documentación en español; identificadores de código en inglés."
        ),
        acceptance_criteria=[
            "existen architecture.md, api-contract.md y data-model.md en ./docs/",
            "el contrato de API cubre todas las funcionalidades M del PRD",
            "cada decisión de stack tiene justificación",
        ],
        expected_output="./docs/architecture.md + api-contract.md + data-model.md",
        critical=True,
    )


def backend_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="backend",
        task=(
            "Como Backend Engineer: implementa EXACTAMENTE ./docs/api-contract.md siguiendo "
            "./docs/architecture.md y ./docs/data-model.md. Incluye: código de la API completa, "
            "validación de inputs, manejo de errores con los códigos del contrato, y tests "
            "(unit + integración) de cada endpoint incluyendo casos de error. Si el contrato "
            "tiene un problema, NO lo cambies: documenta la objeción en NOTES.md y continúa "
            "implementando lo contratado. Código y commits en inglés."
        ),
        acceptance_criteria=[
            "todos los endpoints del contrato implementados",
            "tests de cada endpoint (éxito + error) incluidos",
            "el proyecto arranca sin errores y los tests pasan localmente",
        ],
        expected_output="código backend + tests, según estructura de architecture.md",
        gates=["lint", "tests"],
    )


def frontend_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="frontend",
        task=(
            "Como Frontend Engineer: implementa la interfaz según ./docs/PRD.md (flujos de "
            "usuario) consumiendo EXACTAMENTE ./docs/api-contract.md. Lee NOTES.md: el backend "
            "dejó ahí avisos sobre formatos reales de respuesta. Incluye estados de carga y "
            "error en cada llamada a la API. Código y commits en inglés."
        ),
        acceptance_criteria=[
            "todos los flujos M del PRD son completables desde la UI",
            "cada llamada a la API maneja éxito, carga y error",
            "build del frontend pasa sin errores",
        ],
        expected_output="aplicación frontend según architecture.md",
        gates=["lint", "build"],
    )


def qa_task(project: Project) -> PhaseTask:
    return PhaseTask(
        role="qa",
        task=(
            "Como QA/Tester real: verifica el proyecto entero. (1) Ejecuta la suite de tests "
            "existente. (2) Revisa que CADA endpoint de ./docs/api-contract.md responde según "
            "contrato (éxito y errores). (3) Revisa que los flujos de usuario del PRD funcionan "
            "de punta a punta (front consume back correctamente). Produce ./docs/qa-report.md "
            "con: qué probaste, qué pasó, y una lista accionable de defectos (cómo reproducir, "
            "severidad). Sé escéptico: tu trabajo es ENCONTRAR problemas. NO arregles código: "
            "solo reporta."
        ),
        acceptance_criteria=[
            "existe ./docs/qa-report.md con resultados por endpoint y por flujo",
            "cada defecto tiene reproducción y severidad",
            "veredicto final: APTO o NO-APTO con razones",
        ],
        expected_output="./docs/qa-report.md",
        forbidden=["modificar código de la aplicación (solo reportas)"],
    )


def review_task(project: Project, author_brain: str | None = None) -> PhaseTask:
    return PhaseTask(
        role="review",
        task=(
            "Como Code Reviewer/Auditor: audita el código del proyecto (calidad, seguridad, "
            "mantenibilidad). Busca: secretos hardcodeados, inputs sin validar, inyección "
            "SQL/XSS, errores de lógica, desviaciones del contrato de API. Produce "
            "./docs/review-report.md con hallazgos clasificados (crítico/mayor/menor) y "
            "veredicto APROBADO o RECHAZADO (rechaza si hay críticos)."
        ),
        acceptance_criteria=[
            "existe ./docs/review-report.md con hallazgos clasificados",
            "veredicto justificado",
        ],
        expected_output="./docs/review-report.md",
        forbidden=["modificar código (solo auditas)"],
    )


# phase (state) -> task generator
PHASE_TASKS = {
    "pm": pm_task,
    "architect": architect_task,
    "backend": backend_task,
    "frontend": frontend_task,
    "qa": qa_task,
}
