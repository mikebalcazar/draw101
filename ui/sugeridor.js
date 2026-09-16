/* Sugeridor de comandos  ·  0.20.11. Lo pidió Mike el 16-sep-2026:
 * «si tecleas C, que sugiera COPY o CIRCLE o lo que empiece con C». Mismas
 * reglas que en shape101 (documento «sugeridor-de-comandos-para-draw101»):
 *
 *   1. Primero va lo que Enter correría ahora mismo. Con «C» el programa
 *      corre CIRCULO (es su atajo), así que CIRCULO encabeza aunque COTA sea
 *      más corto. Una sugerencia que no coincide con lo que va a pasar es
 *      peor que no sugerir.
 *   2. Las flechas ya tenían dueño, el historial. Caja vacía: historial;
 *      algo tecleado y hay sugerencias: las flechas eligen. (De paso: antes
 *      teclear «C» y apretar la flecha borraba lo escrito.)
 *   3. Al elegir, el nombre se escribe en la caja: Enter y el espacio corren
 *      lo escrito sin enterarse de que el sugeridor existe.
 *   4. Se busca por nombre y por atajo, en español y en inglés
 *      (Idioma.COMANDOS): quien teclea CIRCLE encuentra CIRCULO.
 *   5. Ocho como mucho, arriba de la caja (la consola vive abajo).
 *   6. Nada se completa solo: flechas y Enter, no Tab.
 */

const Sugeridor = (() => {
  const TOPE = 8;
  let lista = null, elegido = -1, opciones = [];

  const campo = () => document.getElementById("cmd");

  function armar() {
    if (lista) return;
    lista = document.createElement("div");
    lista.id = "sugerencias";
    lista.style.display = "none";
    document.body.appendChild(lista);
  }

  function colocar() {
    const c = campo();
    if (!c) return;
    const r = c.getBoundingClientRect();
    lista.style.left = `${r.left}px`;
    lista.style.width = `${Math.max(340, Math.min(r.width, 720))}px`;
    lista.style.bottom = `${window.innerHeight - r.top + 4}px`;
  }

  /** Nombres en inglés que llevan a un comando en español (Idioma.COMANDOS). */
  function nombresIngles(nombreEs) {
    const mapa = (typeof Idioma !== "undefined" && Idioma.COMANDOS) || {};
    const salida = [];
    for (const [en, es] of Object.entries(mapa)) if (es === nombreEs) salida.push(en);
    return salida;
  }

  /** Los comandos cuyo nombre o atajo (en cualquier idioma) empieza con lo tecleado. */
  function buscar(texto) {
    const t = String(texto || "").trim().toUpperCase();
    if (!t || /[\s,@<]/.test(t) || /^[-\d.]/.test(t) || typeof Comandos === "undefined") return [];
    const todos = Comandos.lista || [];
    const candidatos = [];
    for (const cmd of todos) {
      const nombre = String(cmd.nombre || "").toUpperCase();
      const atajos = (cmd.alias || []).map((a) => String(a).toUpperCase());
      const ingles = nombresIngles(nombre);
      const formas = [nombre, ...atajos, ...ingles];
      const como = formas.find((f) => f.startsWith(t));
      if (!como) continue;
      // Lo que Enter correría con lo tecleado tal cual: nombre, atajo o
      // nombre en inglés que coincide entero.
      const exacto = formas.includes(t);
      candidatos.push({ cmd, como, exacto, ingles });
    }
    candidatos.sort((a, b) => (b.exacto - a.exacto) || (a.cmd.nombre.length - b.cmd.nombre.length) || a.cmd.nombre.localeCompare(b.cmd.nombre));
    return candidatos.slice(0, TOPE);
  }

  function pintar() {
    lista.innerHTML = "";
    const enIngles = typeof Idioma !== "undefined" && Idioma.ingles;
    opciones.forEach((o, i) => {
      const fila = document.createElement("div");
      fila.className = "sug" + (i === elegido ? " on" : "");
      const nom = document.createElement("b");
      nom.textContent = enIngles ? (o.ingles[0] || o.cmd.nombre) : o.cmd.nombre;
      const ayuda = document.createElement("span");
      const atajos = (o.cmd.alias || []).join(", ");
      const otro = enIngles ? "" : (o.ingles[0] ? `  ·  ${o.ingles[0]}` : "");
      ayuda.textContent = (o.cmd.ayuda || "") + (atajos ? `  ·  ${atajos}` : "") + otro;
      fila.append(nom, ayuda);
      fila.onmousedown = (e) => { e.preventDefault(); escoger(i); correrElegido(); };
      lista.appendChild(fila);
    });
    colocar();
    lista.style.display = opciones.length ? "block" : "none";
  }

  function escoger(i) {
    elegido = i;
    const c = campo();
    if (c && opciones[i]) c.value = opciones[i].cmd.nombre;
    pintar();
  }

  function correrElegido() {
    const c = campo();
    if (!c) return;
    const texto = c.value;
    cerrar();
    c.value = "";
    if (typeof Comandos !== "undefined") Comandos.correr(texto);
  }

  function cerrar() {
    elegido = -1;
    opciones = [];
    if (lista) lista.style.display = "none";
  }

  function alTeclear() {
    armar();
    const c = campo();
    // Sólo mientras se está tecleando un comando, no cuando la consola pide un
    // dato a un comando en marcha (una coordenada, una distancia, un texto).
    const pidiendo = typeof Entrada !== "undefined" && (Entrada.activa || Entrada.esperandoTexto);
    opciones = pidiendo ? [] : buscar(c ? c.value : "");
    elegido = -1;
    pintar();
  }

  /** La llama comandos.js antes de tocar el historial. Devuelve true si el
   *  sugeridor se quedó con la flecha. */
  function mover(paso) {
    if (!opciones.length) return false;
    escoger((elegido + paso + opciones.length + (elegido < 0 && paso < 0 ? 1 : 0)) % opciones.length);
    return true;
  }

  function conectar() {
    armar();
    const c = campo();
    if (!c) return;
    c.addEventListener("input", alTeclear);
    c.addEventListener("blur", () => setTimeout(cerrar, 120));
    window.addEventListener("resize", () => { if (opciones.length) colocar(); });
    c.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === "Escape" || e.key === " ") cerrar();
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", conectar);
  else conectar();

  return { mover, cerrar, conectar, buscar, get abierto() { return opciones.length > 0; }, get elegido() { return elegido; } };
})();
