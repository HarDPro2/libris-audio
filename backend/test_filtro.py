"""Filtro de ruido académico — META 3.1"""
import sys; sys.path.insert(0,'.')
import fitz
from extractores import limpiar_bloque, extraer

ok=fallos=0
def check(n,cond,extra=""):
    global ok,fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  '+extra if extra else ''}")
    ok_=cond
    globals().__setitem__('ok', ok+1) if cond else globals().__setitem__('fallos', fallos+1)

def c(n,cond,extra=""):
    global ok,fallos
    print(f"  {'OK  ' if cond else 'FALLO'}  {n}{'  '+extra if extra else ''}")
    if cond: ok+=1
    else: fallos+=1

print("Citas y referencias:")
casos = [
 ("El yo se forma en la infancia (Freud, 1915, p. 43) segun la teoria.", "Freud"),
 ("Como demuestra el estudio (cf. Lacan 1966), el sujeto...", "Lacan"),
 ("Los datos lo confirman (Vygotsky, 1978, pp. 12-18) claramente.", "Vygotsky"),
 ("Segun varios autores [12] y tambien [3, 5] esto es asi.", "[12]"),
 ("Mas info en https://ejemplo.com/articulo y en www.otro.org aqui.", "http"),
 ("Ver doi: 10.1234/abcd.2020 para el detalle.", "doi"),
 ("Escribe a autor@universidad.edu para pedirlo.", "@"),
]
for texto, marca in casos:
    r = limpiar_bloque(texto)
    c(f"elimina {marca!r}", marca not in r, repr(r[:62]))

print("\nNo se pasa de listo:")
conservar = [
 ("La obra de 1915 marco un antes y un despues.", "1915"),
 ("El experimento (que duro tres meses) fue concluyente.", "tres meses"),
 ("La escala va de 1 a 10 en todos los casos.", "1 a 10"),
]
for texto, debe in conservar:
    r = limpiar_bloque(texto)
    c(f"conserva {debe!r}", debe in r, repr(r[:62]))

print("\nConfigurable:")
t = "El yo se forma (Freud, 1915, p. 43) segun la teoria."
c("con filtro apagado mantiene la cita", "Freud" in limpiar_bloque(t, filtro_academico=False))
c("con filtro encendido la quita", "Freud" not in limpiar_bloque(t, filtro_academico=True))

print("\nEncabezados y pies repetidos:")
doc = fitz.open()
for i in range(8):
    p = doc.new_page()
    p.insert_text((72,60),  "Manual de Psicologia Clinica - Capitulo 3", fontsize=9)
    p.insert_text((72,120), f"Contenido unico de la pagina {i+1}. " * 8, fontsize=11)
    p.insert_text((72,780), "Universidad Nacional - 2024", fontsize=9)
d = extraer(doc.tobytes(), "manual.pdf"); doc.close()
apariciones = d.texto.count("Manual de Psicologia Clinica")
c("encabezado repetido eliminado", apariciones == 0, f"aparece {apariciones} veces")
c("pie repetido eliminado", d.texto.count("Universidad Nacional") == 0)
c("contenido real intacto", d.texto.count("Contenido unico") >= 8, f"{d.texto.count('Contenido unico')} paginas")

print("\nCaso real completo:")
t = ("La teoria del apego (Bowlby, 1969, p. 22) sostiene que el vinculo temprano "
     "determina el desarrollo. Vease tambien https://apa.org/apego y el trabajo "
     "de Ainsworth (1978) [4]. El nino construye modelos internos.")
r = limpiar_bloque(t)
print("   antes:", t[:90], "...")
print("   despues:", r[:120])
c("sin citas ni URLs", all(x not in r for x in ("Bowlby","http","[4]","(1978)")))
c("prosa intacta", "teoria del apego" in r and "modelos internos" in r)
c("sin espacios antes de puntuacion", " ." not in r and " ," not in r)

print(f"\n{'='*54}\n{ok} OK · {fallos} fallos")
sys.exit(1 if fallos else 0)
