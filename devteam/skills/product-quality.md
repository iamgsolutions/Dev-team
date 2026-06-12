# SKILL: Calidad de producto — lo que hace VENDIBLE un software

Este equipo construye software que MG Solutions VENDE. Cada decisión de
producto se mide con: ¿un cliente pagaría por esto tal cual está?

- **Estados vacíos**: toda lista/tabla define qué se ve sin datos (mensaje
  útil + acción para crear el primero). Una pantalla en blanco parece rota.
- **Feedback inmediato**: toda acción del usuario produce respuesta visible
  en <1s (spinner, toast, transición). El silencio parece un cuelgue.
- **Errores en humano**: nunca mostrar stacktraces ni "Error 500". Mensaje
  claro + qué puede hacer el usuario. Log técnico aparte para nosotros.
- **Datos realistas en la demo**: sembrar datos de ejemplo coherentes
  (no "asdf", no "test123") — la primera impresión vende.
- **Lo mínimo pulido > lo mucho a medias**: una funcionalidad M perfecta
  vale más que tres S mediocres. Recorta alcance, nunca calidad.
