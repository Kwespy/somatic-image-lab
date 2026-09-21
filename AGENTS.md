# Instrucciones para trabajar en The Somatic Image Lab

## Propósito
El sitio es un espacio experimental para abrir preguntas sobre la imagen. Sus readings funcionan como máquinas de error: confrontan y tensionan textos de referencia que el autor tiene en Google Drive. La investigación busca que los readings se choquen, se mezclen y se contaminen entre sí para producir errores que abran preguntas. Es una idea en evolución; no dar por implementadas sus posibilidades futuras.

## Colaboración
- Conversar en español, con lenguaje claro y pocos tecnicismos. Ejecutar los comandos y revisar sus resultados sin pedir al autor que copie la terminal.
- Discutir las ideas y llevar los experimentos acordados a cambios concretos y pruebas locales. Se pueden modificar estructura y funcionamiento dentro del trabajo solicitado sin pedir permiso por cada decisión rutinaria.
- El diseño tiene una base establecida. La prioridad es el funcionamiento de la idea. La portada y el diseño pueden cambiar cuando el experimento lo justifique; evitar rediseños ajenos al alcance solicitado.
- Preguntar solo por datos necesarios o decisiones conceptuales que no puedan inferirse de la conversación.
- Si un experimento depende de textos de Google Drive, leer las referencias con el acceso disponible o pedir las que falten. No inventar su contenido ni atribuciones.

## Contenido de los readings
- Antes de preparar un reading, revisar los TXT disponibles en Google Drive y los readings publicados. No repetir autora, palabra de error ni conceptos centrales, salvo que la relación sea explícita y justificada.
- Escribir para una persona que no conoce el texto de origen. Definir cada concepto central antes de usarlo: explicar qué nombra, de dónde surge en el texto y por qué importa para la imagen. No encadenar metáforas o términos teóricos sin volverlos concretos.
- Mantener una secuencia legible: «en 1 minuto» presenta el argumento; «tres cosas para conservar» lo condensa; el «punto de arrastre» desarrolla la relación con el reading anterior; «por ejemplo / for example» sitúa el concepto en una situación concreta; «residuo» deja sus consecuencias abiertas; la Máquina de Error fuerza una intervención identificable. Cada sección debe poder entenderse desde la anterior.
- No usar las secciones «proposición incompleta» ni «bifurcación». En su lugar, «por ejemplo / for example» debe probar el concepto con una imagen concreta, una imagen hipotética claramente descrita o una situación reconocible de encuentro con una imagen. Debe reunir ejemplo, prueba de mirada, instrucción de uso y contra-lectura: decir qué se ve o cómo llega la imagen, proponer verificar encuadre, fuente, fecha, secuencia o texto, y explicar cómo interfaz, orden, encuadre, escala y atención organizan una lectura. El ejemplo no debe afirmar sin explicar que una tecnología cambia la imagen; debe explicar qué condiciones de lectura organiza y terminar, cuando sirva, con una pregunta breve.
- En el «punto de arrastre», cuando se nombre un reading anterior, convertir el número y la palabra «reading» en un enlace interno a esa lectura, en español e inglés. Explicar por qué se retoma esa pregunta antes de avanzar hacia el nuevo texto.
- Diferenciar con claridad lo que plantea la autora o el autor de la intervención de TSIL. Cuando el error introduce una palabra externa, explicar de qué campo viene, cómo se aplica al reading y qué pregunta abre.
- Antes de publicar, hacer una lectura editorial en español e inglés: comprobar que una persona pueda responder con el propio texto qué significa cada concepto central y cómo se relaciona con el error. Corregir saltos de sentido, repeticiones y atribuciones imprecisas.

## Experimentos reversibles
- Revisar Git y las instrucciones antes de editar. Conservar los cambios existentes y no sobrescribir trabajo ajeno.
- Antes de un experimento, establecer un punto de retorno: commit existente si el estado está limpio, o copia de los archivos afectados si hay cambios pendientes. Preferir una rama codex/ para experimentos de alcance significativo.
- Mantener los cambios enfocados y explicar qué se probó y cómo volver atrás. No descartar trabajo no relacionado ni reescribir el historial para deshacer un experimento sin autorización.
- Revisar explícitamente los archivos incluidos en cada commit. No incorporar instaladores como Claude.dmg ni archivos ajenos al sitio.

## Idiomas
- El sitio debe ofrecer español e inglés, incluidos nuevos contenidos, controles y mensajes.
- Respetar la elección manual guardada. Si no existe, usar español para navegadores en español e inglés para los demás, siguiendo el comportamiento actual de la portada.
- Probar ambos idiomas y el selector cuando el cambio los afecte. Mantener la documentación personal en español.

## Desarrollo, pruebas y publicación
- Flujo: discutir y desarrollar en este computador, probar localmente, revisar y después publicar en GitHub cuando el autor lo solicite. No hacer push automáticamente durante pruebas o importaciones.
- Es un sitio estático HTML/CSS/JavaScript con scripts Python para preparar lecturas y recursos sociales. Servir desde la raíz con: python3 -B scripts/local_server.py
- Aplicar verificaciones proporcionales: sintaxis y datos, enlaces y recursos locales, e interacciones afectadas en navegador. Para cambios de interfaz, revisar también ambos idiomas y una pantalla estrecha. Informar de pruebas que no se pudieron realizar.
- El lanzador AGREGAR_POST.command llama a scripts/add_post.py, que prepara las lecturas localmente sin generar imágenes, commit ni push. Mantener la publicación como paso separado.
- El botón secreto usa assets/social-export.js y el servicio scripts/local_server.py (puerto 8001). Renderizar solo la imagen solicitada en una carpeta temporal, sin escribir imágenes en readings/. Conservar los recursos antiguos hasta que el autor decida retirarlos.
- Remoto configurado: https://github.com/Kwespy/somatic-image-lab.git. La documentación anterior describe GitHub Pages; no asumir que la configuración remota de Pages está verificada.
- La máquina virtual todavía no existe. No preparar ni ejecutar despliegues a ella salvo que el autor retome expresamente ese trabajo.

## Documentación
Mantener LEEME.txt como guía personal en español, clara y acorde con el funcionamiento real. Distinguir capacidades existentes de ideas y mejoras pendientes.
