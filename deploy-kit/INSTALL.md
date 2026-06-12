# Deploy Kit — Replicar el equipo de desarrollo en un servidor nuevo

Guía para levantar el equipo completo (motor `devteam` + cerebros + skill de Hermes) en otra máquina. Tiempo estimado: 20-40 min, la mayoría en logins.

## Requisitos del servidor

- Windows Server 2022/2025 (o Windows 11). *(Linux: el motor es Python puro y funciona; los scripts de este kit son PowerShell — portar es trivial, ver nota al final.)*
- Acceso a internet y RDP/SSH para los logins.
- **No necesita GPU.** Los cerebros son servicios externos.

## Instalación automática

```powershell
# desde PowerShell como Administrador, en la carpeta del kit:
.\setup.ps1
```

El script (idempotente, se puede re-ejecutar):
1. Verifica/instala: Node.js LTS, Git, GitHub CLI (winget), uv.
2. Instala las CLIs de cerebros: `@anthropic-ai/claude-code`, `@openai/codex`, `opencode-ai` (npm -g).
3. Clona los repos: motor (`hermes-dev-team`) y memoria (`memoria-desarrollo-hermes`).
4. Crea el venv del motor con uv e instala dependencias; ejecuta los tests.
5. Crea la estructura: `C:\Users\<user>\dev\projects\`, `dev\briefs\`.
6. Si detecta una instalación de Hermes, copia la skill `devteam-engine` a sus skills.

## Pasos manuales (logins — siempre humanos)

```powershell
gh auth login          # GitHub: si el navegador falla, usar token PAT (ver HUMAN-LOGINS.md)
claude auth login      # Anthropic (suscripción)
codex login            # ChatGPT (suscripción)
opencode auth login    # pegar API key de OpenRouter (sk-or-...)
```

Verificación: `claude auth status`, `codex login status`, `opencode auth list`, `gh auth status`.

## Configuración del guardián de suscripciones

Por defecto el motor raciona: 15 llamadas/día a Claude, 20 a Codex. Ajustar según el uso humano de esa cuenta:

```powershell
C:\Users\<user>\dev\hermes-dev-team\.venv\Scripts\python.exe -m devteam.cli subs --set claude 10
```

## Verificación final (smoke)

```powershell
$py = "C:\Users\<user>\dev\hermes-dev-team\.venv\Scripts\python.exe"
& $py -m pytest -q                                    # suite del motor (en el dir del motor)
& $py -m devteam.cli new-project ..\memoria-desarrollo-hermes\build\examples\example-brief.md
& $py -m devteam.cli run-task notes --role backend --task "Create hello.md with: Hello" --criteria "hello.md exists"
& $py -m devteam.cli status
```

## Para tener VARIOS equipos en un mismo servidor

Cada equipo = una copia del motor con su propio `DEVTEAM_DATA` y `DEVTEAM_PROJECTS` (variables de entorno que el motor respeta):

```powershell
$env:DEVTEAM_DATA = "C:\teams\equipo2\data"
$env:DEVTEAM_PROJECTS = "C:\teams\equipo2\projects"
```

Con eso, registros, presupuestos y proyectos quedan completamente aislados por equipo.

## Nota Linux

El motor (`devteam`) es Python 3.11 puro sin dependencias de Windows (la resolución de CLIs detecta `.cmd` solo si existe). Las CLIs de cerebros tienen instaladores Linux oficiales. Cambiar rutas de `config.py` vía variables de entorno y portar `setup.ps1` a bash (~30 líneas).
