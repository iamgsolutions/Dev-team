# SKILL: Debugging sistemático — diagnóstico antes que parche

1. **Reproduce primero**: sin reproducción fiable no hay arreglo fiable.
   Reduce al caso mínimo (¿falla con un solo registro? ¿sin auth?).
2. **Lee el error ENTERO**: la última línea del traceback dice QUÉ, las
   primeras dicen DÓNDE empezó. El error real suele ser el PRIMERO de la
   cadena, no el último síntoma.
3. **Una hipótesis cada vez**: formula ("el 404 viene de X porque Y"),
   verifica con UN cambio/log, descarta o confirma. Cambiar 5 cosas a la
   vez = no saber cuál arregló (o rompió) qué.
4. **Bisección**: ¿funcionaba antes? `git log` del archivo; aísla el commit.
   ¿Funciona la capa de abajo? Prueba la query/el service directo sin el router.
5. **El bug arreglado exige**: (a) entender POR QUÉ pasaba (no "ya no pasa"),
   (b) test de regresión, (c) buscar el MISMO patrón en el resto del código
   (los bugs vienen en familias).
6. **Si 30 min sin avanzar**: para, escribe en NOTES.md qué probaste y qué
   descartaste, y replantea (¿la suposición base es falsa?). Insistir a
   ciegas quema tokens sin información nueva.
