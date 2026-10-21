# Mi alarma no hace lo que espero

Esta es una traducción de [troubleshooting.md](troubleshooting.md), traducida por Claude (una IA) y no revisada por un hablante nativo. Avisa de los errores abriendo una issue.

Busca abajo lo que ves. Para cada síntoma: las causas probables, dónde comprobar y qué hacer.

**Mira siempre primero:**

- **Resumen** en el panel: la tarjeta *¿Listo para usar?* nombra lo que falta en los ajustes. *Atención* nombra los sensores con la batería vacía o que no son alcanzables. *Qué vigila cada modo* muestra qué sensores participan en qué modo.
- **Último evento:** la entidad `sensor.vigil_alarm_last_event` y el registro de eventos (`event.vigil_alarm_alarm_events`) dicen qué ocurrió y por qué se rechazó algo.
- **Atributos de la alarma** (`alarm_control_panel.vigil_alarm`): `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## La alarma no se activa

| Ves | Causa | Qué hacer |
|---|---|---|
| `refuse_reason: sensor_open` | Un sensor vigilado está abierto (una ventana, por ejemplo). | Ciérralo, o elige en el sensor qué ocurre si está abierto al activar (anular, esperar a que se cierre, rechazar). |
| `refuse_reason: sensor_unavailable` | Un sensor no es alcanzable (batería vacía, fuera de alcance). | Mira *Atención* para saber cuál. Repáralo o anúlalo. |
| `refuse_reason: alarm_condition` | Hay una alarma de incendio, gas o sabotaje activa. | Elimina la causa y desactiva primero. |
| `refuse_reason: not_disarmed` | La alarma ya está activada o en el retardo de salida. | Desactiva primero. |
| Un error sobre el código | Código incorrecto, demasiado corto, no permitido para ese modo o bloqueado (véase abajo). | Comprueba el usuario en la pestaña *Usuarios*. |

## La alarma no se dispara con una puerta abierta o movimiento

1. **¿Está realmente activada la alarma?** Durante el retardo de salida (`arming`) aún no se vigila nada.
2. **¿Está el sensor en un grupo de sensores?** Un sensor de intrusión sin grupo no vigila nada. Si *Qué vigila cada modo* dice «ningún grupo de sensores», crea los grupos predeterminados (tarjeta *¿Listo para usar?*).
3. **¿Está el grupo activo en este modo?** *Interior* solo vale para Fuera, por ejemplo. En En casa un detector de movimiento nunca se dispara.
4. **¿Está el sensor anulado?** Entonces figura en `bypassed_sensors`. Una anulación termina al desactivar.
5. **¿Es el tipo «retardado»?** Entonces primero tienes el retardo de entrada (`pending`), y la alarma solo se dispara si no desactivas a tiempo.
6. **¿Hay una regla de confirmación?** Entonces la alarma solo se dispara cuando suficientes sensores distintos se disparan dentro de la ventana de tiempo. Un solo sensor solo da el aviso «sin confirmación».
7. **¿Es el sensor no alcanzable?** Entonces no puede dispararse. Mira *Atención*.
8. **¿Es la entidad correcta?** En *Herramientas para desarrolladores → Estados*, comprueba que la entidad pasa realmente a `on` cuando se abre la puerta.

## No llega ninguna notificación a mi teléfono

1. ¿Hay un **canal de notificación**? Si no, *¿Listo para usar?* lo dice y ofrece tu teléfono.
2. ¿Están activadas las **categorías** correctas? Solo se envían mensajes de esas categorías (alarma, retardo de entrada, avería, técnico).
3. ¿Hay un **retraso**? Un canal de escalada con un retraso de 30 segundos solo notifica pasados 30 segundos, y no si antes desactivas o confirmas.
4. Usa el **botón de prueba** del canal. Si la prueba no llega, el problema es Home Assistant o la app, no la alarma: comprueba el permiso de notificaciones de la app en tu teléfono.
5. ¿Es correcto el **servicio**? Debe ser un servicio `notify.` existente.

## La sirena no suena

1. ¿Hay una sirena configurada, y suena para *esta causa* (intrusión, incendio, gas, sabotaje, avería)?
2. Prueba la acción `vigil_alarm.test_siren`. Si no suena, el problema es la propia entidad (no alcanzable, batería vacía).
3. ¿Se **silenció** la sirena con `vigil_alarm.silence`? Entonces la alarma sigue activa pero la sirena calla.
4. ¿Ha pasado la **duración máxima**? Después la sirena se detiene sola.

## Mi código se rechaza

- **Demasiado corto:** la longitud mínima está en *Ajustes* (de 4 a 12 caracteres).
- **Bloqueado:** tras algunos códigos incorrectos Vigil bloquea ese lugar de forma escalonada (por defecto 5, luego 15, luego 60 minutos), también para el código correcto. Espera un momento; el registro de eventos muestra `code_locked`. Si muestra `code_locked_permanent`, el teclado permanece cerrado hasta que un administrador pulse *Levantar el bloqueo* en Paneles. Los valores están en *Ajustes*, *Bloqueo*.
- **No permitido:** el usuario solo puede usar ciertos modos. Comprueba *Modos permitidos*. Desactivar siempre funciona con un código válido.

## Falsas alarmas

- Da a las puertas el tipo **retardado** con un retardo de entrada, para poder desactivar a tiempo.
- Deja que un detector de movimiento vigile solo en Fuera (grupo *Interior*).
- Usa una **regla de confirmación**: una alarma solo si dos detectores de movimiento se disparan en un minuto.
- Para una notificación, mira el registro de eventos para ver qué sensor fue.

## Sin notificaciones de batería o sabotaje

- El sensor necesita un **sensor de batería**. *¿Listo para usar?* nombra los sensores que no lo tienen. También sirve un dispositivo que solo informa «batería baja» (encendido/apagado).
- Si el dispositivo tiene un **sensor de sabotaje**, indícalo en el sensor. La tarjeta nombra los sensores de sabotaje que no están conectados a nada.

## Un rechazo está en un idioma distinto del esperado

Cuando una tarjeta estándar de Home Assistant (por ejemplo el mosaico con los botones de activación) muestra un rechazo, el texto está en el idioma **configurado en Home Assistant** (*Ajustes, Sistema, General*), no en el de tu perfil, y sin nombre de usuario: *El modo Personalizado no puede ser activado por usted.* Vigil tiene los textos en seis idiomas (inglés para cualquier otro). La tarjeta Vigil y el teclado táctil muestran el rechazo en el idioma del teclado.

## Las entidades se llaman distinto de lo que esperaba

Los identificadores de entidad de Vigil siempre terminan en el nombre en inglés, incluso cuando Home Assistant está en otro idioma (por ejemplo `binary_sensor.vigil_alarm_intrusion_alarm`). Lo que ves en la interfaz sigue tu propio idioma. Comprueba los nombres reales en *Ajustes → Dispositivos y servicios → Vigil Alarm*. Si vienes de una versión anterior, actualiza tus automatizaciones y paneles de control a los nuevos identificadores (véanse las notas de la versión).

## El panel está vacío

Recarga el navegador forzando (Ctrl+F5) y comprueba que la integración se está ejecutando en *Dispositivos y servicios*. Si no, mira el registro (*Ajustes → Sistema → Registros*, busca `vigil`).

## ¿Sigue sin funcionar?

Descarga el diagnóstico (*Dispositivos y servicios → Vigil Alarm → ⋮ → Descargar diagnóstico*), que no contiene códigos ni nombres de personas, e infórmalo en GitHub (véase la pestaña *Acerca de*).

## Sigo recibiendo un recordatorio de prueba de sirena

El recordatorio se repite hasta que se hace una prueba. Toca *Probar la sirena* en el mensaje, usa *Probar la sirena ahora* en la pestaña Resumen o llama a `vigil_alarm.test_siren`. Para detener los recordatorios, pon el intervalo en *Ajustes* a 0.

## El heartbeat falla

La tarjeta *Heartbeat* de la pestaña Resumen nombra el motivo: *sin conexión* (Home Assistant no llega a internet o la dirección es incorrecta), *sin respuesta en 10 segundos*, o *HTTP 404* y similares (el servicio no conoce la dirección; cópiala de nuevo). Corrígela en *Ajustes* y haz clic en *Probar ahora*.
