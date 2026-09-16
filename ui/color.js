/* Elegir color  ·  Mike (16-sep-2026): «cuando quiero cambiar de color en las
 * propiedades de un layer o de una entidad, sólo me salen códigos de color.
 * Implementa una paleta de colores predeterminados y un selector de RGB».
 *
 * Antes: en la entidad, una lista con los colores que ya usaban las capas,
 * escritos como «#808080»; en la capa, el cuadrito de color de Windows y nada
 * más. Ahora los dos abren lo mismo:
 *
 *   · los nueve colores del índice de AutoCAD (rojo, amarillo, verde, cian,
 *     azul, magenta, blanco/negro, gris y gris claro), que son los que trae
 *     cualquier plano que llegue de fuera;
 *   · los de Taller 101, para que un plano nuestro se vea como los nuestros;
 *   · una fila de grises, que es lo que más se usa para los fondos;
 *   · el selector del sistema (RGB, el de Windows) para cualquier otro;
 *   · y la caja del código, para quien ya sabe cuál quiere o lo trae copiado.
 *
 * `Color.boton(valor, opciones)` devuelve un botón que enseña el color y abre
 * la paleta; el valor se lee en `boton.valor` y se avisa por `onelegir`.
 */

const Color = (() => {
  /* Los nueve primeros del índice de AutoCAD: es lo que trae un DWG de fuera y
   * lo que el taller nombra por número («ponlo en el 1»). */
  const ACAD = [
    ["#FF0000", "1 · rojo"], ["#FFFF00", "2 · amarillo"], ["#00FF00", "3 · verde"],
    ["#00FFFF", "4 · cian"], ["#0000FF", "5 · azul"], ["#FF00FF", "6 · magenta"],
    ["#FFFFFF", "7 · blanco/negro"], ["#808080", "8 · gris"], ["#C0C0C0", "9 · gris claro"],
  ];
  const T101 = [
    ["#0080C1", "Taller 101"], ["#00A9E0", "Taller 101 claro"], ["#1A1F27", "Tinta"],
    ["#B4712A", "Canto"], ["#2F7D4F", "Bien"], ["#A8422A", "Peligro"],
  ];
  const GRISES = ["#000000", "#333333", "#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#FFFFFF"];

  const hex = (v) => {
    const t = String(v || "").trim().toUpperCase();
    const m = t.match(/^#?([0-9A-F]{6})$/) || t.match(/^#?([0-9A-F]{3})$/);
    if (!m) return null;
    const c = m[1];
    return "#" + (c.length === 3 ? c[0] + c[0] + c[1] + c[1] + c[2] + c[2] : c);
  };

  let abierta = null;

  function cerrar() {
    if (abierta) { abierta.remove(); abierta = null; }
  }

  /** Abre la paleta junto a `ancla`. `alElegir(color|null)`; null = «por capa». */
  function abrir(ancla, valor, { porCapa = false, alElegir } = {}) {
    cerrar();
    const caja = document.createElement("div");
    caja.className = "paleta";
    abierta = caja;

    const elegir = (v) => { cerrar(); if (alElegir) alElegir(v); };

    if (porCapa) {
      const b = document.createElement("button");
      b.className = "porcapa" + (valor ? "" : " on");
      b.textContent = Tr("Por capa");
      b.onclick = () => elegir(null);
      caja.appendChild(b);
    }

    const rejilla = (titulo, lista) => {
      const t = document.createElement("div");
      t.className = "tit";
      t.textContent = titulo;
      caja.appendChild(t);
      const r = document.createElement("div");
      r.className = "rej";
      for (const item of lista) {
        const [v, nombre] = Array.isArray(item) ? item : [item, item];
        const b = document.createElement("button");
        b.className = "muestra" + (hex(valor) === v ? " on" : "");
        b.style.background = v;
        b.title = nombre;
        b.onclick = () => elegir(v);
        r.appendChild(b);
      }
      caja.appendChild(r);
    };

    rejilla(Tr("Los de siempre"), ACAD);
    rejilla(Tr("Taller 101"), T101);
    rejilla(Tr("Grises"), GRISES);

    // Los que ya usa el dibujo: sale gratis y evita inventar un color nuevo
    // cada vez que se quiere el mismo azul de la capa de cotas.
    const usados = [...new Set(((((estado || {}).resumen) || {}).capas || []).map((c) => c.color))]
      .filter((c) => hex(c)).slice(0, 12);
    if (usados.length) rejilla(Tr("Los de este dibujo"), usados);

    const pie = document.createElement("div");
    pie.className = "pie";
    const rgb = document.createElement("input");
    rgb.type = "color";                       // en Electron abre el de Windows
    rgb.value = hex(valor) || "#0080C1";
    rgb.title = Tr("Elegir cualquier color (RGB)");
    rgb.oninput = () => { texto.value = rgb.value.toUpperCase(); };
    rgb.onchange = () => elegir(rgb.value.toUpperCase());
    const texto = document.createElement("input");
    texto.type = "text";
    texto.className = "codigo";
    texto.value = hex(valor) || "";
    texto.placeholder = "#RRGGBB";
    texto.onkeydown = (e) => {
      if (e.key === "Enter") { const v = hex(texto.value); if (v) elegir(v); }
      if (e.key === "Escape") cerrar();
    };
    pie.append(rgb, texto);
    caja.appendChild(pie);

    document.body.appendChild(caja);
    const r = ancla.getBoundingClientRect();
    const c = caja.getBoundingClientRect();
    let x = Math.min(r.left, window.innerWidth - c.width - 8);
    let y = r.bottom + 4;
    if (y + c.height > window.innerHeight) y = Math.max(4, r.top - c.height - 4);
    caja.style.left = `${Math.max(4, x)}px`;
    caja.style.top = `${y}px`;
    setTimeout(() => {
      document.addEventListener("mousedown", fuera, { once: true });
    }, 0);
    function fuera(e) { if (abierta && !abierta.contains(e.target)) cerrar(); }
    return caja;
  }

  /** Un botón que enseña el color y abre la paleta al picarlo. */
  function boton(valor, { porCapa = false, alElegir } = {}) {
    const b = document.createElement("button");
    b.className = "boton-color";
    b.type = "button";
    const pinta = (v) => {
      b.valor = v || null;
      b.style.background = v || "transparent";
      b.classList.toggle("porcapa", !v);
      b.textContent = v ? "" : Tr("Por capa");
      b.title = v || Tr("Por capa");
    };
    pinta(hex(valor));
    b.onclick = () => abrir(b, b.valor, {
      porCapa,
      alElegir: (v) => { pinta(v); if (alElegir) alElegir(v); },
    });
    b.pintar = pinta;
    return b;
  }

  return { boton, abrir, cerrar, hex, ACAD, T101, GRISES };
})();

window.Color = Color;
