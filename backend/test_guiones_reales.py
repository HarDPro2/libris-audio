"""Los 149 casos REALES salidos de la biblioteca de HarDP (97 libros).

Estos fragmentos son los que imprimio `reparar_libros.py` el 12-09-2026. La
version sin diccionario pegaba los 62 del bloque GUION, y de ahi salieron
"septiembreoctubre", "pareceque" y "locurairrumpe".

Esta prueba necesita el diccionario empaquetado (backend/diccionarios/).
"""
import sys
from collections import Counter

from calidad import Diccionario
from guiones import decidir_union

# UNIR  = era un corte de palabra: se pegan los dos trozos
# GUION = el guion era un guion de verdad (rango, compuesto o raya de inciso):
#         NO se pega, el texto se deja como esta
CASOS = [
 ("UNIR","desgracia","da"),("UNIR","espo","sos"),("UNIR","ha","bía"),
 ("UNIR","en","contrarla"),("UNIR","si","guiente"),("UNIR","cor","pulenta"),
 ("UNIR","malen","tendidos"),("UNIR","descon","certante"),("UNIR","profesio","nalidad"),
 ("UNIR","tecno","logía"),("UNIR","Maes","tro"),("UNIR","testa","rudez"),
 ("UNIR","co","mún"),("UNIR","obte","ner"),("UNIR","sen","tido"),
 ("UNIR","enten","derse"),("UNIR","rea","lizado"),("UNIR","Capí","tulo"),
 ("UNIR","mate","riales"),("UNIR","obsti","nado"),("UNIR","dan","do"),
 ("UNIR","jo","ven"),("UNIR","fas","cina"),("UNIR","indivi","duo"),
 ("UNIR","suje","to"),("UNIR","téc","nica"),("UNIR","so","bre"),
 ("UNIR","du","dosos"),("UNIR","elegi","dos"),("UNIR","im","píos"),
 ("UNIR","mandamien","tos"),("UNIR","por","que"),("UNIR","tie","nes"),
 ("UNIR","arre","glar"),("UNIR","apóya","te"),("UNIR","nad","ie"),
 ("UNIR","directamen","te"),("UNIR","for","mar"),("UNIR","escla","va"),
 ("UNIR","obtie","ne"),("UNIR","lle","gada"),("UNIR","len","guaje"),
 ("UNIR","cele","braban"),("UNIR","Des","pués"),("UNIR","cau","sa"),
 ("UNIR","du","rante"),("UNIR","conce","dida"),("UNIR","recon","ciliación"),
 ("UNIR","ocupa","ción"),("UNIR","tempe","ramento"),("UNIR","jun","tos"),
 ("UNIR","igua","les"),("UNIR","cír","culo"),("UNIR","psicoanalí","ticos"),
 ("UNIR","cambian","te"),("UNIR","entendi","miento"),("UNIR","buscán","dose"),
 ("UNIR","desem","peñado"),("UNIR","traduci","do"),("UNIR","perso","nalidad"),
 ("UNIR","compa","ñía"),("UNIR","diaman","te"),("UNIR","bos","que"),
 ("UNIR","suce","dió"),("UNIR","regre","sé"),("UNIR","con","traste"),
 ("UNIR","espe","cial"),("UNIR","pe","sar"),("UNIR","difer","entes"),
 ("UNIR","acti","tud"),("UNIR","uni","verso"),("UNIR","án","geles"),
 ("UNIR","indepen","dientes"),("UNIR","socieda","des"),("UNIR","den","tro"),
 ("UNIR","ais","lado"),("UNIR","dete","ner"),("UNIR","lu","minosa"),
 ("UNIR","mu","ros"),("UNIR","circuns","tantes"),("UNIR","exa","gerando"),
 ("UNIR","cris","talizada"),("UNIR","individ","ual"),("UNIR","psi","cología"),
 ("UNIR","al","gunos"),("UNIR","fortu","na"),("UNIR","combi","no"),
 ("GUION","septiembre","octubre"),("GUION","luso","brasileiro"),
 ("GUION","lobos","y"),("GUION","cabeza","hacia"),("GUION","creer","es"),
 ("GUION","parece","que"),("GUION","locura","irrumpe"),("GUION","dicción","de"),
 ("GUION","histórico","es"),("GUION","hereditario","ha"),("GUION","egoísmo","acuden"),
 ("GUION","reservas","de"),("GUION","escépticos","nos"),("GUION","entonces","no"),
 ("GUION","medio","se"),("GUION","teólogos","que"),("GUION","rostro","de"),
 ("GUION","diámetro","que"),("GUION","día","y"),
 ("GUION","sensorio","motor"),("GUION","causa","efecto"),("GUION","chino","japonesa"),
 ("GUION","serio","cómico"),("GUION","hombre","sándwich"),("GUION","auto","stop"),
 ("GUION","colibríes","polilla"),("GUION","Quijote","ni"),("GUION","Quijote","que"),
 ("GUION","posadero","no"),("GUION","repitió","a"),("GUION","obispo","un"),
 ("GUION","decía","es"),("GUION","nadie","me"),("GUION","otra","y"),
 ("GUION","ahora","en"),("GUION","persona","y"),("GUION","exacta","no"),
 ("GUION","radical","socialismo"),("GUION","sordomudo","el"),("GUION","fuera","y"),
 ("GUION","oral","el"),("GUION","padre","no"),("GUION","desenlace","se"),
 ("GUION","cielo","hay"),("GUION","trabajo","como"),("GUION","mente","y"),
 ("GUION","sociales","y"),("GUION","todo","es"),("GUION","Maga","se"),
 ("GUION","yo","que"),("GUION","Terencio","el"),("GUION","rostro","era"),
 ("GUION","conservar","una"),("GUION","inseguras","de"),("GUION","burla","en"),
 ("GUION","joven","donde"),("GUION","dijo","de"),("GUION","lectores","la"),
 ("GUION","después","lo"),("GUION","modestia","ha"),("GUION","verde","profundos"),
]

# ---------------------------------------------------------------------------
# Los pegotes REALES de "Asi hablo Zaratustra" — el libro donde la raya de
# dialogo llego como guion y la version sin diccionario pego 53 uniones.
#
# PEGOTES   = hay que deshacerlos
# CORRECTAS = palabras buenas que el diccionario no reconoce (enclitico o
#             prefijo) y que la primera version de despegar_texto rompia
# ---------------------------------------------------------------------------
PEGOTES = [
 "lobosy", "dicciónde", "locurairrumpe", "cabezahacia", "pareceque",
 "creeres", "buenay", "unsobre", "ypredicadores", "estabancomo",
 "enpensamiento", "Ycuando", "erandemasiado", "buenosy", "aquelque",
 "amigonecesita", "mihermano", "juecessiempre", "lasemejanza", "creadoresde",
 "locurasen", "perohermanos", "unapiel", "hablanasí", "limosnade",
 "siempreda", "parael", "misesperanzas", "harátu", "débilse",
 "pescarbuenos", "Zaratustraen", "montemonte",
 # segunda pasada, con --desde: los que si son pegotes
 "Concienzudoasí", "montañafortaleza", "ángelescaricaturas", "éltierna",
 "comúnel", "Améndiciendo", "gobernantesy", "quenadie", "siemprepor",
 "mismola", "tiesosasí", "vezque", "enseñocon", "loscortesanos", "cruzen",
 "bienno", "hombreme", "másese", "serpienteno", "orejaen", "torcidasme",
 "lamiel", "preferiblementeun", "pescadoresen", "cosaspescar",
]

# En MODO ESTRICTO solo se recupera lo que lleva palabra de funcion detras.
# Es el dano real de Schopenhauer, el unico que la version vieja pudo causar.
PEGOTES_ESTRICTOS = [
 "concienciaes", "hogarson", "uniónun", "perdersees", "humanidadque",
]
CORRECTAS = [
 "persuadirlo", "escuchadlo", "contempladlo",    # verbo + enclitico
 "desaprendemos", "desaprender", "desaprende",   # prefijo + palabra
 "irrealizado",
 "insondablemente", "pensativamente",            # adverbio en -mente
 "Desconﬁado",                                   # ligadura "fi" de PDF viejo
 # De Analectas, Schopenhauer y Ana Karenina: 48 palabras CORRECTAS que la
 # version laxa destrozaba. Son la razon de que el modo estricto exista.
 "Fangshu", "Ziyuan", "Serica", "Zhonggong",              # nombres chinos
 "habere", "nihilo", "extemplo", "perdere",               # latin
 "parfait", "jamais", "mademoiselles",                    # frances
 "Durand", "Milton", "Prusia", "Venevsky", "FruFru",      # nombres propios
 "Rusias", "recodos", "hurras", "troikas", "jockeys",     # plurales
 "blusitas", "cuerpecitos", "padrecitos", "cabecitas", "añosos",
 "mujercita", "madrecita", "casaquita", "vaquería",       # diminutivos
 "Limitóse", "Sentóse", "acomodóse", "Acercóse",          # enclitico + pret.
 "persignóse", "habríase", "habíase", "Proponíase",
 "Distinguíanse", "hacíanlo", "presentándoselo",
 "exponiéndole", "atrayéndole", "sirviéndole",            # prefijo + gerundio
 "ocultamiento", "barrancada", "rental", "familial",
]

# Frecuencias plausibles del libro: las palabras de funcion altisimas, las de
# contenido medias. Es lo que decide donde va el corte.
FREC_ZARATUSTRA = Counter({
 "y": 1200, "de": 900, "que": 800, "el": 700, "la": 650, "en": 500,
 "es": 400, "se": 380, "lo": 350, "un": 300, "una": 280, "no": 300,
 "como": 200, "para": 190, "su": 180, "al": 150, "mi": 120, "si": 100,
 "tu": 90, "así": 90, "me": 80, "pero": 80, "nos": 70, "cuando": 70,
 "te": 60, "mis": 60, "sobre": 60, "siempre": 60, "buena": 45, "eran": 45,
 "hermanos": 45, "buenos": 38, "estaban": 35, "pensamiento": 40,
 "hacia": 40, "aquel": 40, "da": 20, "buen": 30, "demasiado": 30, "ay": 25,
 "parece": 31, "amigo": 55, "hermano": 50, "Zaratustra": 90,
 "zaratustra": 90, "cabeza": 22, "locura": 20, "creer": 18,
 "predicadores": 18, "monte": 16, "creadores": 14, "esperanzas": 13,
 "necesita": 12, "hablan": 12, "valentía": 11, "piel": 10, "jueces": 9,
 "hará": 9, "aprender": 9, "débil": 8, "locuras": 8, "lobos": 7,
 "fidelidad": 7, "dicción": 6, "semejanza": 6, "limosna": 5,
 "concienzudo": 5, "realizado": 5, "irrumpe": 4, "escuchad": 4,
 "aprendemos": 4, "pescar": 4, "contemplad": 3, "persuadir": 3,
 "septiembre": 2, "octubre": 2, "ir": 2, "des": 1,
 # las que NO se deben tocar aunque el diccionario no las conozca
 "son": 70, "fue": 40, "eran": 45, "está": 30, "están": 25,
 "s": 40, "e": 30, "l": 20, "d": 15, "os": 25, "ni": 60, "ex": 10,
 "recodo": 3, "rusia": 9, "kitty": 80, "hurra": 4, "troika": 5,
 "blusita": 2, "cuerpecito": 2, "padrecito": 3, "cabecita": 2,
 "jockey": 6, "mademoiselle": 7, "años": 30, "mujer": 90, "cita": 8,
 "madre": 60, "casa": 80, "quita": 4, "va": 30, "quería": 25,
 "oculta": 5, "miento": 3, "renta": 4, "familia": 40, "limitó": 12,
 "sentó": 15, "acomodó": 6, "acercó": 14, "persignó": 3, "habría": 20,
 "había": 200, "proponía": 5, "distinguían": 3, "hacían": 8,
 "presentándose": 2, "haber": 40, "hilo": 7, "templo": 6, "mil": 9,
 "duran": 3, "par": 12, "fait": 2, "ja": 5, "mais": 2, "perder": 18,
 "perderse": 4, "fang": 3, "shu": 3, "zi": 4, "yuan": 3, "zhong": 3,
 "gong": 3, "rica": 9, "ve": 20, "nevsky": 2, "fru": 4, "sir": 3,
 "viéndole": 2, "poniéndole": 3, "trayéndole": 2, "a": 200,
 "barranca": 3, "prusia": 4, "p": 8, "unión": 9, "humanidad": 22,
 "conciencia": 35, "hogar": 12,
 "concienzudo": 6, "montaña": 14, "fortaleza": 9, "ángeles": 11,
 "caricaturas": 4, "él": 200, "tierna": 5, "común": 22, "amén": 3,
 "diciendo": 18, "gobernantes": 7, "nadie": 30, "por": 250, "mismo": 40,
 "tiesos": 3, "vez": 45, "enseño": 6, "los": 400, "cortesanos": 5,
 "cruz": 8, "bien": 70, "hombre": 120, "más": 180, "ese": 35,
 "serpiente": 12, "oreja": 6, "torcidas": 3, "miel": 9,
 "preferiblemente": 3, "pescadores": 4, "cosas": 30, "insondable": 4,
 "pensativa": 3, "mente": 15, "aprende": 6, "conﬁado": 2,
 "tambien": 60, "habia": 80, "razon": 9, "corazon": 11, "mision": 7,
 "conclusion": 5, "operacion": 4, "bienestar": 4, "desgraciada": 6,
 "encontrarla": 3, "con": 90, "ocio": 2,
})

# ---------------------------------------------------------------------------
# Espacios que faltan — parrafo REAL de "El libro de los espiritus" (Kardec),
# parte 100. Es el problema que de verdad estropea ese libro; los 17 guiones
# que tiene son legitimos.
# ---------------------------------------------------------------------------
PARRAFO_KARDEC = (
    "les ha dadoeste aspecto, los rodean delos más exquisitos cuidados, "
    "que seuniese a vuestras filas, tiene ademásotra utilidad, "
    "accesiblesa los consejos, Estaes el deber."
)
PEGADAS_ESPERADAS = ["dado este", "se uniese", "además otra",
                     "accesibles a", "Esta es"]

FREC_KARDEC = Counter({
    "dado": 30, "este": 120, "de": 900, "los": 700, "se": 400, "uniese": 2,
    "además": 40, "otra": 35, "accesibles": 3, "a": 800, "esta": 90,
    "es": 500, "dad": 1, "oeste": 1, "recodo": 3, "codos": 2, "re": 1,
    "renta": 4, "duran": 3, "rusia": 9, "mujer": 90, "cita": 8, "años": 30,
    "hurra": 4, "troika": 5, "limitó": 12, "sentó": 15,
})

# LIMITES CONOCIDOS — no fallan la prueba, pero quedan escritos.
# Extranjerismos donde NINGUNO de los dos lados esta en un diccionario
# espanol: no hay senal para distinguirlos de un corte. Una aparicion en
# toda la biblioteca (Asimov), y el resultado es un termino pegado, no una
# palabra destruida.
LIMITES = [("GUION", "walkie", "talkie")]


def main():
    dic = Diccionario()
    if not dic.disponible:
        sys.exit("No encuentro el diccionario. Falta backend/diccionarios/es_ES.{aff,dic}")
    es_valida = lambda w: dic.existe(w) or dic.existe(w.lower())   # noqa: E731
    vacio: Counter = Counter()      # sin pistas del documento: el peor caso

    fallos = []
    for esperado, izq, der in CASOS:
        r = decidir_union(izq, der, vacio, es_valida)
        got = "UNIR" if (r is not None and "-" not in r) else "GUION"
        if got != esperado:
            fallos.append((esperado, got, izq, der, r))

    print(f"  {len(CASOS) - len(fallos)} OK · {len(fallos)} fallos "
          f"sobre {len(CASOS)} casos reales")
    for esp, got, izq, der, r in fallos:
        print(f"    esperaba {esp:6} obtuvo {got:6}  «{izq}- {der}» -> {r!r}")

    # --- Deshacer lo que la version vieja pego: los 39 casos de Zaratustra ---
    from guiones import despegar_texto
    for w in PEGOTES:
        _, n = despegar_texto(w, FREC_ZARATUSTRA, es_valida, estricto=False)
        if not n:
            fallos.append(("PARTIR", "no toca", w, "", ""))
    print(f"  despegar: {len(PEGOTES) - sum(1 for f in fallos if f[0] == 'PARTIR')}"
          f"/{len(PEGOTES)} pegotes reales deshechos")

    # Las palabras correctas han de sobrevivir en MODO ESTRICTO, que es el de
    # por defecto. En laxo muchas de ellas se rompen: por eso laxo solo vale
    # cuando hay muchas partes intactas que sirvan de coartada, como pasaba en
    # Zaratustra, y por eso hay que pedirlo a mano con --laxo.
    danos = []
    for w in CORRECTAS:
        salida, n = despegar_texto(w, FREC_ZARATUSTRA, es_valida)
        if n:
            danos.append(f"{w} -> {salida}")
            fallos.append(("NO PARTIR", "partida", w, "", salida))
    print(f"  despegar: {len(danos)} palabras correctas rotas (debe ser 0)")
    for d in danos:
        print(f"    DANO  {d}")

    rotas_en_laxo = sum(1 for w in CORRECTAS
                        if despegar_texto(w, FREC_ZARATUSTRA, es_valida,
                                          estricto=False)[1])
    print(f"  (en modo laxo se romperian {rotas_en_laxo} de {len(CORRECTAS)}: "
          f"por eso el estricto es el de por defecto)")

    estrictos = sum(1 for w in PEGOTES_ESTRICTOS
                    if despegar_texto(w, FREC_ZARATUSTRA, es_valida)[1])
    print(f"  estricto: {estrictos}/{len(PEGOTES_ESTRICTOS)} pegotes con "
          f"palabra de funcion recuperados")
    if estrictos != len(PEGOTES_ESTRICTOS):
        fallos.append(("estricto", str(estrictos), "", "", ""))

    # La coartada: una palabra que sale en partes que nunca se tocaron venia
    # del libro, no de la reparacion. "adivinose" es el caso real: puede ser
    # "adivinose" con enclitico, y solo la coartada lo resuelve.
    frec_ad = Counter(FREC_ZARATUSTRA)
    frec_ad.update({"adivino": 3, "se": 380})
    _, n_sin = despegar_texto("adivinose", frec_ad, es_valida)
    _, n_con = despegar_texto("adivinose", frec_ad, es_valida,
                              evitar={"adivinose"})
    print(f"  coartada: sin ella parte ({n_sin}), con ella respeta ({n_con})")
    if not (n_sin == 1 and n_con == 0):
        fallos.append(("coartada", f"{n_sin}/{n_con}", "adivinose", "", ""))

    # Y las palabras sin tilde que un algoritmo tonto romperia.
    sin_tilde = ("tambien habia razon corazon mision conclusion operacion "
                 "bienestar desgraciada encontrarla")
    salida, tocadas = despegar_texto(sin_tilde, FREC_ZARATUSTRA, es_valida)
    print(f"  despegar: {tocadas} palabras sin tilde tocadas (debe ser 0)")
    if tocadas:
        fallos.append(("sin tilde", str(tocadas), "", "", salida))

    # --- Espacios que faltan ---
    from guiones import separar_pegadas
    reg: list = []
    salida, n = separar_pegadas(PARRAFO_KARDEC, FREC_KARDEC, es_valida, reg)
    puestos = [b for _, b in reg]
    print(f"  espacios: {n}/{len(PEGADAS_ESPERADAS)} arreglados en el parrafo "
          f"real de Kardec")
    for esperado in PEGADAS_ESPERADAS:
        if esperado not in puestos:
            fallos.append(("espacios", "no lo arregla", esperado, "", salida))

    rotas = []
    for w in CORRECTAS + ["recodos", "mujercita", "rental", "Durand"]:
        _, k = separar_pegadas(w, FREC_KARDEC, es_valida)
        if k:
            rotas.append(w)
            fallos.append(("espacios", "parte una buena", w, "", ""))
    print(f"  espacios: {len(rotas)} palabras correctas partidas (debe ser 0)")

    # Sin diccionario se pegaba TODO: es la prueba de que la regla hace falta.
    pegados = sum(1 for e, i, d in CASOS
                  if e == "GUION" and decidir_union(i, d, vacio) == i + d)
    for esperado, izq, der in LIMITES:
        r = decidir_union(izq, der, vacio, es_valida)
        got = "UNIR" if (r is not None and "-" not in r) else "GUION"
        if got != esperado:
            print(f"    (limite conocido: «{izq}- {der}» -> {r!r})")

    print(f"  sin diccionario se pegaban mal {pegados} de "
          f"{sum(1 for e, _, _ in CASOS if e == 'GUION')} guiones de verdad")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
