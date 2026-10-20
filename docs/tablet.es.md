# Una tableta en la pared como teclado de alarma

Esta es una traducción de [tablet.md](tablet.md), traducida por Claude (una IA) y no revisada por un hablante nativo. Avisa de los errores abriendo una issue.

Puedes manejar Vigil con una tableta que muestre un panel de control de Home Assistant, en lugar del teclado ESPHome (o junto a él). La tableta es un panel en el registro, vinculado a un usuario de Home Assistant, y muestra la **tarjeta Vigil**: el estado, los botones de los modos que puede usar, un teclado numérico y, tras el código de instalador del panel, los sensores.

## Configurarla

1. **Crea un usuario para la tableta.** En Home Assistant: *Ajustes → Personas → Usuarios → Añadir usuario*. Usa un usuario normal. Puedes elegir en su lugar una cuenta de administrador (aparece como *(admin)* en la lista), pero es responsabilidad tuya: los ajustes del panel se aplican entonces a todo lo que esa cuenta hace, en cada dispositivo en el que esté conectada, y un dispositivo robado o desatendido está conectado como administrador. Vigil no da a una cuenta así derechos de administrador en el panel (siempre hace falta un código para desactivar y anular), y la mejor vía es una segunda cuenta normal para el uso diario.
2. **Registra la tableta en Vigil.** Abre *Vigil Alarm → Paneles → Añadir panel*. Dale un nombre, elige *Tableta o teléfono con Home Assistant* como tipo de dispositivo y elige la cuenta en *Cuenta de Home Assistant (tableta o teléfono)*. Ajusta lo que puede hacer la tableta (modos, desactivar, anular, silenciar, lista de sensores, idioma), exactamente como para un panel ESPHome. Define un **código de instalador** para el panel si la tableta debe poder mostrar los sensores.
3. **Inicia sesión en la tableta con ese usuario** y abre un panel de control con la tarjeta Vigil. En el editor del panel de control elige *Añadir tarjeta → Personalizada: Vigil*, o en YAML:

   ```yaml
   type: custom:vigil-card
   ```

   Vigil carga la tarjeta por sí mismo; no hay nada que instalar ni que añadir como recurso. La tarjeta no tiene ajustes salvo `idle_timeout` (segundos sin tocar antes de que olvide un código a medio teclear, predeterminado 30). Para una tableta de pared usa una vista de panel (una sola tarjeta) o un panel de control tipo quiosco, como el que puede mostrar Fully Kiosk Browser, para que la barra lateral quede oculta.
4. Usa **HTTPS** para Home Assistant. Con un simple `http://` el código viaja legible por tu Wi-Fi.

## Qué hace la tarjeta

![La tarjeta en un teléfono: no lista, teclado numérico, activando con cuenta atrás, alarma](images/card-phone-states-en.png)

![La tarjeta en una tableta: dos columnas, anillo y cuenta atrás a la izquierda, botones y teclado numérico a la derecha](images/card-tablet-states-en.png)

Con un teclado (una tableta que lo tenga, o un ordenador) puedes teclear el código: dígitos, Retroceso para borrar, Intro para confirmar, Esc para cerrar el teclado numérico.

La tarjeta muestra el estado como un anillo con un icono, del color del estado; durante los retardos de salida y de entrada el anillo es la cuenta atrás. Sigue el ancho en el que está: una columna en un teléfono, dos columnas en una tableta. Tiene el mismo aspecto que el teclado táctil.

- Sigue el perfil del panel de la tableta: solo los modos en los que ese panel puede activar, *Desactivar* solo si puede, los botones de anulación solo si puede anular, el idioma que elegiste para el panel, y ninguna lista de sensores cuando está en *nunca*.
- **Desactivar y anular siempre piden un código de usuario**; activar solo pide uno si *código necesario para activar* está activado. El teclado numérico nunca se abre solo: durante el retardo de entrada y una alarma la pantalla muestra primero lo que ocurre, y quien quiera desactivar pulsa *Desactivar*.
- **La lista de sensores** se abre con el código de cualquier usuario de Vigil, o el código de instalador del panel (mediante `vigil_alarm.unlock_panel`), durante el tiempo ajustado. Anular y restablecer exigen un usuario con el derecho de anular (sensores de sabotaje: el derecho adicional de sabotaje). Hasta entonces la tarjeta solo muestra *cuántos* sensores están abiertos, nunca sus nombres. Salir de la lista, o 30 segundos sin tocar, hace que la tarjeta olvide el desbloqueo.
- **Particiones:** la tarjeta muestra *Vigil Alarm* y la partición (o *Todas*) que maneja, también con una sola partición. Con varias, unas fichas permiten cambiar; tras el tiempo de retorno (*Ajustes*, *Pantalla del panel*) vuelve a la partición predeterminada del panel.
- Un usuario que no está vinculado a un panel ve *No vinculado*; un panel bloqueado muestra *Bloqueado* y no hace nada.

## Qué impone Vigil

- Vigil reconoce la tableta por el **usuario de Home Assistant** detrás de cada llamada. Home Assistant lo pone él mismo, así que no se puede imitar enviando otro texto `source`. Esto es más fuerte que para un panel ESPHome, cuyas llamadas no llevan usuario.
- Muestre lo que muestre la tarjeta, decide el servidor: una llamada que el perfil no permite se rechaza y se registra (`panel_refused`). La tarjeta es solo una cara más bonita encima.
- La tableta tiene su propio temporizador de bloqueo para códigos incorrectos, y Vigil nunca la trata como administrador. *Bloqueado* rechaza todo de esa tableta; *Levantar el bloqueo* y *Desbloquear* funcionan como en cualquier panel.
- Un teléfono apagado no es una avería: para una tableta o un teléfono *Vigilar si este panel es alcanzable* está desactivado por defecto, así que ni Reparación ni mensaje. Actívalo para una tableta que cuelga de la pared todo el día.
- El historial muestra quién lo hizo, por ejemplo *Anna (hall-tablet)*.

## Sin conexión

La tarjeta saluda a Vigil cada minuto mientras el panel de control está abierto. Si Vigil no ha oído nada de ella en 10 minutos, recibes una Reparación *Panel no alcanzable* y un mensaje en tus canales de averías (`panel_offline`, y `panel_online` cuando vuelve), igual que para un panel ESPHome. El estado de la alarma nunca cambia por ello. La lista de paneles muestra *Tarjeta Vigil activa* para una tableta que ha saludado.

- Solo se vigila una tableta cuya tarjeta ha saludado al menos una vez. Una tableta que muestra la tarjeta de alarma propia de Home Assistant no puede decir nada, así que nunca se informa de ella.
- Vigil recuerda que una tableta usa la tarjeta, de modo que una que esté muerta al reiniciar Home Assistant se informa igualmente, diez minutos después del reinicio.
- Una tableta con la pantalla apagada y el navegador cerrado está, para Vigil, sin conexión. Deja que una tableta de pared mantenga abierto el panel de control.

## Qué no hace

- Home Assistant no tiene permisos por entidad. El usuario de la tableta puede llamar a cualquier servicio que un usuario normal pueda llamar y leer todos los estados. Vigil protege la alarma (códigos, perfil, bloqueo) y la tarjeta solo pide lo que el perfil permite, pero el usuario aún puede salir del panel de control. No des a ese usuario más de lo que la tableta necesita.
- La tarjeta de alarma propia de Home Assistant sigue funcionando para una tableta, pero muestra todos los modos (un modo que el perfil no permite se rechaza al pulsarlo) y no tiene lista de sensores.
- La tarjeta no tiene página de información como el panel ESPHome; para eso la tableta tiene Home Assistant.
- Si roban la tableta: pon el panel en *Bloqueado* en Vigil, y desactiva el usuario en Home Assistant o elimina sus tokens de actualización (*Perfil → Seguridad*).

## Dos cuentas para el administrador y un candado en el navegador

El punto débil de todo panel de control es la cuenta que hay detrás. Vigil nunca restringe a un administrador, así que un administrador que permanece conectado en una tableta o un teléfono da a ese dispositivo todos los derechos. Mantén tu **cuenta de administrador solo para administrar**, y crea una segunda cuenta normal para el uso diario (y para la tableta, si quieres una). Bloquea el navegador de la tableta en el panel de control (un navegador de quiosco como Fully Kiosk Browser, o el modo quiosco de Home Assistant) para que un visitante no pueda salir de él.

Dos cosas protegen la alarma de un transeúnte ante una tableta de pared: Vigil trata la cuenta de la tableta como una normal, sea lo que sea en Home Assistant (siempre hace falta un código para desactivar y anular), y **activar** también necesita un código si activas *Código necesario para activar* en la pestaña Ajustes. Ese ajuste vale para todo el sistema: cuando está desactivado, cualquiera que pueda pulsar el botón puede activar.

## Un teléfono o una tableta: el mismo registro

Una tableta en la pared y el teléfono de un compañero de piso se tratan igual: ambos son una entrada de la pestaña *Paneles* vinculada a una cuenta de Home Assistant (el campo *Cuenta de Home Assistant (tableta o teléfono)*, preferiblemente una cuenta normal; también se puede elegir un administrador, con la cautela descrita arriba). Por entrada ajustas lo que puede hacer (modos, desactivar, anular, silenciar, lista de sensores, idioma), exactamente como para un panel ESPHome, y la lista de sensores sigue en todas partes las mismas reglas: oculta hasta que el código de instalador de la entrada la desbloquea. La única diferencia es cómo Vigil reconoce el dispositivo: un panel ESPHome por su identificador de panel, una cuenta por el usuario detrás de la llamada.

- **Cualquier código válido funciona** en un dispositivo así, y el historial muestra de quién era el código, por ejemplo *Bob (cleo-phone)*. Sin código, sin operación (donde hace falta un código).
- **Cada entrada tiene su propio temporizador de bloqueo**: códigos incorrectos en el teléfono de Cleo bloquean ese teléfono (de forma escalonada, véase *Ajustes*, *Bloqueo*), no la tableta ni a nadie más.
- **Solo las cuentas registradas pueden operar.** En cuanto hay una cuenta registrada, cualquier otra cuenta ordinaria de Home Assistant (por ejemplo la de los niños) se rechaza antes de que se examine ningún código (evento `user_refused`, el error *El usuario no está registrado*), y eso no cuenta para un bloqueo. Los administradores, las automatizaciones, los scripts y los paneles ESPHome (llamadas sin usuario de Home Assistant) no se ven afectados. Mientras no haya ninguna cuenta registrada no cambia nada, así que una actualización desde una versión anterior no cambia nada.
