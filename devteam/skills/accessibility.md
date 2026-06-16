# SKILL: Accesibilidad (a11y) — usable por todos, exigible por empresas

## Vendemos a empresas; muchas requieren accesibilidad por contrato/ley.

### Lo no negociable (WCAG práctico)
- **Semántica**: usa elementos nativos (`<button>`, `<nav>`, `<main>`, `<label>`)
  antes que `<div>` con onClick. El HTML correcto es accesible gratis.
- **Labels**: todo input con `<label>` asociado (o `aria-label`). Botones con
  texto (no solo icono; si es icono, `aria-label`).
- **Teclado**: TODO lo operable con ratón debe serlo con teclado (Tab/Enter/
  Esc). Foco visible siempre (no quites el outline sin sustituirlo).
- **Contraste**: texto normal ≥ 4.5:1, grande ≥ 3:1. Nada de gris claro sobre
  blanco.
- **Imágenes**: `alt` descriptivo (o `alt=""` si es decorativa).
- **Estado dinámico**: cambios importantes (errores de formulario, toasts)
  anunciados con `aria-live`. Errores ligados al input con `aria-describedby`.

### Formularios (donde más se falla)
- Error por campo, junto al campo, con texto (no solo color rojo).
- No deshabilites el submit sin explicar por qué; valida y muestra qué falta.

### Verificación rápida
- Navega la pantalla SOLO con teclado: ¿puedes completar el flujo?
- ¿Los lectores de pantalla anunciarían cada control? (roles/labels presentes).
- Si hay color como única señal (rojo=error), añade icono/texto.
