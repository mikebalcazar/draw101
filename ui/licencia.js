/* La suscripción, vista desde la app  ·  0.20.20
 *
 * draw101 se vende por suscripción mensual (Mike, 16-sep-2026) y se corta si
 * no se paga. El motor de todo eso —firma, huella de la máquina, activar,
 * latido— vive en `core/licencia.py`; aquí está lo único que ve quien usa el
 * programa:
 *
 *   · **Pantalla de activación** al arrancar sin licencia. Sale una vez por
 *     sesión, no en cada clic: quien todavía no compra no tiene por qué
 *     pelearse con un cuadro cada rato.
 *   · **Panel** (comando LICENCIA, o Ayuda ▾): en qué está la suscripción,
 *     hasta cuándo, y los dos botones que importan —activar aquí, o soltar
 *     esta computadora para poder activar otra—.
 *   · **Latido**: una vez al arrancar, unos segundos después de que la
 *     interfaz ya está viva, y luego cada 24 h. Es lo que corre la fecha de
 *     corte cuando el pago sigue al día. Si no hay red no pasa nada y no se
 *     dice nada: el permiso ya trae hasta 30 días de margen.
 *   · **Aviso de que vence**, desde 7 días antes, una vez por sesión.
 *   · **Marca de modo lectura** en la barra, y los botones de guardar y
 *     exportar apagados, **cuando el corte esté encendido**.
 *
 * Sobre eso último: en la 0.20.20 el corte está **apagado** a propósito
 * (`core/licencia.CORTA = False`, decisión de Mike del 19-sep-2026). Todo lo
 * de arriba funciona y se ve, pero guardar y exportar siguen libres. El motor
 * es quien manda: esta interfaz no decide si se puede escribir, se lo
 * pregunta (`puede_escribir` y `corta` vienen en cada respuesta). Así el día
 * que se encienda el corte no hay que tocar nada de aquí, y —más importante—
 * nadie se queda sin guardar por un error de este archivo.
 */

const Licencia = (() => {
  let ultimo = null;                  // lo último que dijo el motor
  let avisadoEnSesion = false;        // el aviso de «vence en N días», una vez
  let ofrecidoEnSesion = false;       // la pantalla de activación, una vez
  const temporizadores = [];

  const CADA = 24 * 60 * 60 * 1000;   // el latido, una vez al día

  /* Cómo se dice cada estado, en el idioma del taller y no en el del
   * servidor. Quien usa draw101 no tiene por qué leer «sin_activar». */
  const COMO_SE_LLAMA = {
    activa: "Al corriente",
    por_vencer: "Por vencer",
    vencida: "Vencida",
    sin_activar: "Sin activar",
  };

  /** El día de una fecha del servidor, escrito como se escribe aquí. Vienen
   * en ISO con hora («2026-10-18T02:40:11.000Z») y la hora no le importa a
   * nadie: lo que se pregunta es hasta qué día. */
  function dia(iso) {
    if (!iso) return "";
    const d = new Date(String(iso).slice(0, 10) + "T12:00:00");
    if (isNaN(d)) return String(iso).slice(0, 10);
    const donde = (typeof Idioma !== "undefined" && Idioma.ingles) ? "en-US" : "es-MX";
    return d.toLocaleDateString(donde, { year: "numeric", month: "long", day: "numeric" });
  }

  /* --- Lo que se ve sin abrir nada ------------------------------------- */

  /** La marca de «modo lectura» en la barra de arriba, y los botones de
   * escribir apagados. Sólo cuando el corte de verdad muerde: apagar botones
   * que sí funcionan sería mentir al revés. */
  function pintar() {
    const corta = !!(ultimo && ultimo.corta);
    const lectura = corta && ultimo && !ultimo.puede_escribir;

    let marca = document.getElementById("marca-lectura");
    if (lectura && !marca) {
      marca = document.createElement("span");
      marca.id = "marca-lectura";
      marca.textContent = Tr("Modo lectura");
      marca.title = Tr("Sin suscripción activa: se puede ver, medir e imprimir, pero no guardar ni exportar.");
      marca.onclick = () => panel();
      const donde = document.querySelector(".archivo");
      if (donde) donde.parentNode.insertBefore(marca, donde);
    } else if (!lectura && marca) {
      marca.remove();
    }

    for (const id of ["#b-guardar", "#b-guardar-como", "#b-exportar"]) {
      const b = document.querySelector(id);
      if (!b) continue;
      b.disabled = lectura;
      b.title = lectura ? Tr("Sin suscripción activa no se puede guardar ni exportar.") : "";
    }
  }

  /** Guarda lo que contestó el motor y repinta. */
  function apuntar(r) {
    ultimo = r || null;
    pintar();
    return ultimo;
  }

  /* --- Activar ---------------------------------------------------------- */

  /** Pide la clave y la canjea. Devuelve `true` si quedó activada. */
  async function activar(pista) {
    const v = await Dialogo.abrir({
      titulo: Tr("Activar draw101"),
      pista: pista || Tr("Escribe la clave de suscripción que te dio Taller 101."),
      ancho: "440px",
      campos: [
        { clave: "clave", etiqueta: Tr("Clave"), tipo: "texto", valor: "",
          marcador: "T101-XXXX-XXXX-XXXX" },
        { clave: "nota", tipo: "nota", etiqueta: "", valor:
          Tr("La clave queda ligada a esta computadora. Para pasarla a otra, suelta ésta primero desde el mismo cuadro.") },
      ],
      aceptar: Tr("Activar"),
      validar: (v) => (String(v.clave || "").trim().length >= 8
        ? null : Tr("Falta la clave (T101-XXXX-XXXX-XXXX).")),
    });
    if (!v) return false;
    try {
      apuntar(await post("/api/licencia/activar", { clave: v.clave }));
      avisar(F("draw101 quedó activado: {0}, hasta el {1}.",
        ultimo.cliente || Tr("suscripción"), dia(ultimo.hasta)));
      return true;
    } catch (e) {
      // El motivo viene ya traducido del motor («esa clave no existe», «no
      // está pagada»…): se enseña tal cual y se vuelve a ofrecer, que es lo
      // que uno quiere cuando se equivocó de tecla.
      avisar(Tr(e.message), true, 9000);
      return await activar(Tr(e.message));
    }
  }

  /** Suelta esta computadora, preguntando antes: es una acción que le quita
   * a alguien lo que tiene abierto. */
  async function soltar() {
    const v = await Dialogo.abrir({
      titulo: Tr("Soltar esta computadora"),
      pista: Tr("Se libera el lugar de esta máquina para poder activar otra. Aquí draw101 queda sin activar."),
      campos: [],
      aceptar: Tr("Soltar"),
    });
    if (!v) return;
    apuntar(await post("/api/licencia/desactivar"));
    avisar(Tr("Esta computadora quedó suelta: el lugar está libre para otra."));
  }

  /* --- El panel --------------------------------------------------------- */

  /** Comando LICENCIA y Ayuda ▾: en qué está la suscripción y qué se puede
   * hacer con ella. */
  async function panel() {
    try { apuntar(await api("/api/licencia")); } catch (_) { /* con lo último que se sepa */ }
    const e = ultimo || { estado: "sin_activar" };
    const activa = e.estado === "activa" || e.estado === "por_vencer";

    // Un renglón por cosa, para que se lea de corrido y no haya que
    // interpretar una tabla de cuatro celdas vacías.
    const renglones = [`${Tr("Estado")}: ${Tr(COMO_SE_LLAMA[e.estado] || e.estado)}`];
    if (e.cliente) renglones.push(`${Tr("Cliente")}: ${e.cliente}`);
    if (e.plan) renglones.push(`${Tr("Plan")}: ${e.plan}`);
    if (e.hasta) renglones.push(`${Tr("Vigente hasta")}: ${dia(e.hasta)}`);
    if (e.estado === "por_vencer") renglones.push(F("Quedan {0} día(s).", e.dias));
    if (!e.corta) renglones.push(Tr("Por ahora draw101 no corta: se puede guardar y exportar aunque no esté activado."));
    else if (!e.puede_escribir) renglones.push(Tr("Modo lectura: se puede ver, medir e imprimir, pero no guardar ni exportar."));

    const campos = [{ clave: "resumen", tipo: "nota", etiqueta: "",
                      valor: renglones.join("\n") }];
    if (e.mensaje) campos.push({ clave: "mensaje", tipo: "nota", etiqueta: "", valor: Tr(e.mensaje) });

    const v = await Dialogo.abrir({
      titulo: Tr("Suscripción de draw101"),
      pista: activa ? "" : Tr("draw101 se vende por suscripción mensual."),
      ancho: "460px",
      campos,
      aceptar: activa ? Tr("Soltar esta computadora") : Tr("Activar…"),
      cancelar: Tr("Cerrar"),
    });
    if (!v) return;
    if (activa) await soltar(); else await activar();
  }

  /* --- Al arrancar ------------------------------------------------------ */

  /** Lee el estado, ofrece activar si hace falta y avisa si está por vencer.
   * Nada de esto estorba: si el motor no contesta, no pasa nada. */
  async function revisar({ ofrecer = true } = {}) {
    try { apuntar(await api("/api/licencia")); } catch (_) { return null; }
    const e = ultimo;
    if (e.estado === "por_vencer" && !avisadoEnSesion) {
      avisadoEnSesion = true;
      avisar(Tr(e.mensaje), false, 12000);
    }
    if (ofrecer && e.ofrecer_al_arrancar !== false && !ofrecidoEnSesion
        && (e.estado === "sin_activar" || e.estado === "vencida")) {
      ofrecidoEnSesion = true;
      await bienvenida(e);
    }
    return e;
  }

  /** La pantalla de activación del arranque. No es un cuadro que atrape: si
   * no se quiere activar ahora, se sigue. Con el corte apagado eso significa
   * seguir trabajando; con el corte encendido, seguir en modo lectura, y lo
   * dice el propio botón para que nadie se lleve una sorpresa. */
  async function bienvenida(e) {
    const seguir = e.corta ? Tr("Seguir en modo lectura") : Tr("Ahora no");
    const v = await Dialogo.abrir({
      titulo: e.estado === "vencida" ? Tr("La suscripción venció") : Tr("Activar draw101"),
      pista: Tr(e.mensaje),
      ancho: "460px",
      campos: [
        { clave: "clave", etiqueta: Tr("Clave"), tipo: "texto", valor: "",
          marcador: "T101-XXXX-XXXX-XXXX" },
        { clave: "nota", tipo: "nota", etiqueta: "", valor:
          Tr("¿No tienes clave? Pídela a Taller 101. La suscripción es mensual y se puede soltar de una computadora para pasarla a otra.") },
      ],
      aceptar: Tr("Activar"),
      cancelar: seguir,
      validar: (v) => (String(v.clave || "").trim().length >= 8
        ? null : Tr("Falta la clave (T101-XXXX-XXXX-XXXX).")),
    });
    if (!v) return;
    try {
      apuntar(await post("/api/licencia/activar", { clave: v.clave }));
      avisar(F("draw101 quedó activado: {0}, hasta el {1}.",
        ultimo.cliente || Tr("suscripción"), dia(ultimo.hasta)));
    } catch (err) {
      avisar(Tr(err.message), true, 9000);
    }
  }

  /** El latido: le pregunta al servidor si sigue pagada y corre la fecha.
   * Nunca levanta y nunca avisa de que falló: sin red, el margen del permiso
   * hace su trabajo. */
  async function latido() {
    try { apuntar(await post("/api/licencia/latido")); } catch (_) { /* nada */ }
  }

  /** Lo que corre solo al arrancar. Como el de actualizaciones: unos segundos
   * después, para no pelear con la carga del dibujo. */
  function programar() {
    temporizadores.push(setTimeout(async () => {
      await revisar();
      await latido();
    }, 2500));
    temporizadores.push(setInterval(latido, CADA));
  }

  return { revisar, panel, activar, soltar, latido, programar, pintar,
           temporizadores, get estado() { return ultimo; } };
})();

Comandos.registrar({
  nombre: "LICENCIA", alias: ["LICENSE", "SUSCRIPCION", "SUBSCRIPTION", "ACTIVAR", "ACTIVATE"],
  ayuda: "La suscripción de draw101: cómo está, activar o soltar esta computadora",
  correr: () => Licencia.panel(),
});

/* Las pruebas apagan los temporizadores:
 * `Licencia.temporizadores.forEach(clearTimeout)`. */
window.addEventListener("load", () => Licencia.programar());
window.Licencia = Licencia;
