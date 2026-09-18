"""Comprobar una firma Ed25519, sin instalar nada  ·  0.20.18

draw101 tiene que poder decir «esta licencia la firmó Taller 101 y nadie más».
Eso es una firma digital, y el Python que va dentro del instalador no trae
ninguna biblioteca de criptografía (se comprobó el 17-sep-2026: ni cryptography
ni pynacl). Meter una engordaría el instalador y habría que compilarla para
Windows; verificar Ed25519 son doscientas líneas de aritmética con enteros, que
Python hace de fábrica. Así que va aquí.

**Sólo verifica.** Firmar es del servidor, con la llave privada, que nunca sale
de ahí; draw101 lleva únicamente la llave pública. Con la pública no se puede
fabricar un permiso: ésa es toda la gracia del asunto.

La aritmética es la de la RFC 8032 (curva edwards25519), escrita a la manera
de la propia RFC. No es código que haya que entender para trabajar en draw101:
lo que hay que saber es que `verificar(llave, mensaje, firma)` contesta `True`
sólo si esa firma la hizo la llave privada que corresponde a esa pública.

Está probado contra vectores generados con una biblioteca de verdad
(`cryptography`, que se usa **sólo para hacer las pruebas**, nunca dentro del
programa). Ver `pruebas/t033_licencia.py`.
"""

from __future__ import annotations

import hashlib

# --- La curva  ·  RFC 8032, sección 5.1 ------------------------------------
P = 2 ** 255 - 19                     # el primo del cuerpo
L = 2 ** 252 + 27742317777372353535851937790883648493   # el orden del grupo
D = -121665 * pow(121666, P - 2, P) % P
RAIZ_MENOS_UNO = pow(2, (P - 1) // 4, P)


def _sha512(datos: bytes) -> int:
    return int.from_bytes(hashlib.sha512(datos).digest(), "little")


def _inverso(x: int) -> int:
    return pow(x, P - 2, P)


def _recuperar_x(y: int, signo: int) -> int | None:
    """La x del punto de la curva que tiene esa y. `None` si no existe."""
    if y >= P:
        return None
    x2 = (y * y - 1) * _inverso(D * y * y + 1) % P
    if x2 == 0:
        return None if signo else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = x * RAIZ_MENOS_UNO % P
    if (x * x - x2) % P != 0:
        return None
    if x % 2 != signo:
        x = P - x
    return x


# Los puntos van en coordenadas extendidas (X, Y, Z, T): así sumar no necesita
# divisiones, que son lo caro. Ver RFC 8032, sección 5.1.4.
def _sumar(p, q):
    px, py, pz, pt = p
    qx, qy, qz, qt = q
    a = (py - px) * (qy - qx) % P
    b = (py + px) * (qy + qx) % P
    c = 2 * pt * qt * D % P
    e = 2 * pz * qz % P
    # E, F, G, H de la RFC; el punto sale como (X, Y, Z, T) = (EF, GH, FG, EH).
    ee, ff, gg, hh = b - a, e - c, e + c, b + a
    return (ee * ff % P, gg * hh % P, ff * gg % P, ee * hh % P)


def _por_escalar(p, n: int):
    r = (0, 1, 1, 0)                   # el neutro
    while n > 0:
        if n & 1:
            r = _sumar(r, p)
        p = _sumar(p, p)
        n >>= 1
    return r


def _comprimir(p) -> bytes:
    x, y, z, _ = p
    zi = _inverso(z)
    x, y = x * zi % P, y * zi % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _descomprimir(s: bytes):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    signo = y >> 255
    y &= (1 << 255) - 1
    x = _recuperar_x(y, signo)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


#: El punto base de la curva (RFC 8032, sección 5.1).
_GY = 4 * _inverso(5) % P
_GX = _recuperar_x(_GY, 0)
BASE = (_GX, _GY, 1, _GX * _GY % P)


def verificar(llave_publica: bytes, mensaje: bytes, firma: bytes) -> bool:
    """¿Esa firma de ese mensaje la hizo la privada de esa pública?

    Nunca levanta una excepción: una llave rota, una firma de otro tamaño o
    unos bytes cualesquiera contestan `False`. Del otro lado hay una app que
    tiene que abrir o no abrir, no tronar.
    """
    try:
        if len(llave_publica) != 32 or len(firma) != 64:
            return False
        a = _descomprimir(llave_publica)
        if a is None:
            return False
        # Una llave de orden chico (la de ceros, por ejemplo) acepta cualquier
        # firma: no es un agujero aquí —nuestra pública va escrita en el
        # programa— pero una llave así sólo aparece por error o por alguien
        # jugando, y más vale que no abra nada. Multiplicar por 8 la manda al
        # neutro si es de ésas.
        if _comprimir(_por_escalar(a, 8)) == _comprimir((0, 1, 1, 0)):
            return False
        r = _descomprimir(firma[:32])
        if r is None:
            return False
        s = int.from_bytes(firma[32:], "little")
        if s >= L:                     # firma no canónica: se rechaza
            return False
        h = _sha512(firma[:32] + llave_publica + mensaje) % L
        # Se compara sB = R + hA, que es la ecuación de la firma.
        izq = _por_escalar(BASE, s)
        der = _sumar(r, _por_escalar(a, h))
        return _comprimir(izq) == _comprimir(der)
    except Exception:
        return False
