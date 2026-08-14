package com.librisaudio.app.data.model

import com.librisaudio.app.ui.components.BookBindingStyle

/**
 * META 3.7 — enlace género ↔ marco ↔ música ambiental.
 *
 * Dos saltos independientes:
 *
 *   categoría del libro  ──estiloPara()──>  BookBindingStyle (marco 3D + FX + tipografía)
 *   BookBindingStyle     ──pistasPara()──>  pistas recomendadas
 *
 * El "mood" NO vive en BackgroundMusicCatalog.kt porque ese archivo lo
 * regenera backend/subir_musica.py y se perdería en la siguiente subida.
 * Aquí se indexa por nombre de archivo, que es estable: mientras el MP3 se
 * llame igual en R2, conserva su mood aunque el catálogo se regenere entero.
 */
enum class MusicMood {
    SERENO,       // neutro, de fondo, no compite con la voz
    ROMANCE,      // cálido, lírico
    MELANCOLIA,   // nostálgico, tono menor
    MISTERIO,     // oscuro, tenso
    EPICO,        // amplio, con impulso
    LIGERO,       // alegre, ágil
    SOLEMNE,      // grave, ceremonial
    ENSUENO       // etéreo, flotante
}

object GenreMusic {

    // ── 1. Mood por archivo ──────────────────────────────────────────────
    // Clave = nombre del MP3 en R2 (sin ruta). Si una pista nueva no está
    // aquí, cae en SERENO: sigue apareciendo en el selector y sirve de fondo
    // neutro para cualquier género, nunca desaparece de la lista.
    private val MOOD_POR_ARCHIVO: Map<String, MusicMood> = mapOf(
        "arabesque_no_1_string_quartet_arr.mp3"                              to MusicMood.ENSUENO,
        "arabesque_no_1_andantino_con_moto.mp3"                              to MusicMood.ENSUENO,
        "nocturne_in_b_flat_minor_op_9_no_1.mp3"                             to MusicMood.MELANCOLIA,
        "nocturne_in_d_flat_major_op_27_no_2.mp3"                            to MusicMood.ROMANCE,
        "nocturne_in_e_flat_major_op_9_no_2.mp3"                             to MusicMood.ROMANCE,
        "nocturne_in_f_minor_op_55_no_1.mp3"                                 to MusicMood.MELANCOLIA,
        "nocturnes_op_32_no_2_nocturne_in_ab_major.mp3"                      to MusicMood.ROMANCE,
        "paul_pitman_moonlight_sonata_op_27_no_2_ii_allegretto.mp3"          to MusicMood.SERENO,
        "piano_sonata_no_14_in_csm_moonlight_op_27_no_2_i_adagio_sostenuto.mp3" to MusicMood.MISTERIO,
        "romance_de_juegos_prohibidos.mp3"                                   to MusicMood.MELANCOLIA,
        "santa_lucia.mp3"                                                    to MusicMood.LIGERO,
        "violin_concerto_in_d_major_op_61_iii_rondo_allegro.mp3"             to MusicMood.EPICO,
        "violin_concerto_in_d_op_61_i_allegro_ma_non_troppo.mp3"             to MusicMood.EPICO,
        "violin_partita_no_2_bwv_1004_4_giga_guitar_arrangement.mp3"         to MusicMood.LIGERO,
        "violin_partita_no_2_bwv_1004.mp3"                                   to MusicMood.SOLEMNE
    )

    fun moodDe(track: MusicTrack): MusicMood =
        MOOD_POR_ARCHIVO[track.streamUrl.substringAfterLast('/')] ?: MusicMood.SERENO

    // ── 2. Moods por marco, en orden de preferencia ──────────────────────
    // El primero es el que mejor encaja; los siguientes son el plan B para
    // que ningún género se quede sin música si el catálogo cambia.
    fun moodsPara(estilo: BookBindingStyle): List<MusicMood> = when (estilo) {
        BookBindingStyle.CLASSIC    -> listOf(MusicMood.SERENO, MusicMood.SOLEMNE, MusicMood.ENSUENO)
        BookBindingStyle.MEDIEVAL   -> listOf(MusicMood.SOLEMNE, MusicMood.EPICO)
        BookBindingStyle.SPIRITUAL  -> listOf(MusicMood.ENSUENO, MusicMood.SERENO, MusicMood.SOLEMNE)
        BookBindingStyle.WAR        -> listOf(MusicMood.EPICO, MusicMood.SOLEMNE)
        BookBindingStyle.LOVE       -> listOf(MusicMood.ROMANCE, MusicMood.MELANCOLIA)
        BookBindingStyle.PARANORMAL -> listOf(MusicMood.MISTERIO, MusicMood.MELANCOLIA)
        BookBindingStyle.SCIENTIFIC -> listOf(MusicMood.SERENO, MusicMood.ENSUENO)
        BookBindingStyle.COMEDY     -> listOf(MusicMood.LIGERO)
        BookBindingStyle.FANTASY    -> listOf(MusicMood.ENSUENO, MusicMood.EPICO)
        BookBindingStyle.POETRY     -> listOf(MusicMood.MELANCOLIA, MusicMood.ENSUENO, MusicMood.ROMANCE)
        BookBindingStyle.NOIR       -> listOf(MusicMood.MISTERIO, MusicMood.MELANCOLIA)
        BookBindingStyle.COSMIC     -> listOf(MusicMood.ENSUENO, MusicMood.MISTERIO)
    }

    /**
     * Pistas recomendadas para un marco, ordenadas por lo bien que encajan.
     * Nunca devuelve lista vacía: si ningún mood casa, cae al catálogo entero,
     * porque quedarse sin música de fondo es peor que una elección imperfecta.
     */
    fun pistasPara(estilo: BookBindingStyle): List<MusicTrack> {
        val orden = moodsPara(estilo)
        val recomendadas = BackgroundMusicCatalog.tracks
            .filter { moodDe(it) in orden }
            .sortedBy { orden.indexOf(moodDe(it)) }
        return recomendadas.ifEmpty { BackgroundMusicCatalog.tracks }
    }

    /** La mejor pista para un marco, o null si el catálogo está vacío. */
    fun pistaSugerida(estilo: BookBindingStyle): MusicTrack? = pistasPara(estilo).firstOrNull()

    // ── 3. Categoría del libro -> marco ──────────────────────────────────
    // Se busca por palabra clave sobre categoría + título normalizados, no por
    // igualdad exacta, porque la categoría de un libro subido por el usuario es
    // texto libre: puede venir "Terror", "novela negra", "Sci-Fi" o vacía.
    private val CLAVES: List<Pair<List<String>, BookBindingStyle>> = listOf(
        listOf("poesia", "poema", "verso", "soneto")                       to BookBindingStyle.POETRY,
        listOf("religion", "espiritual", "biblia", "sagrado", "mistica",
               "fe ", "oracion", "zen", "budis", "autoayuda", "superacion",
               "motivac", "habitos", "mindfulness", "meditac")             to BookBindingStyle.SPIRITUAL,
        listOf("ciencia ficcion", "sci-fi", "scifi", "cosmos", "espacial",
               "galax", "distop")                                          to BookBindingStyle.COSMIC,
        listOf("fantasia", "fantasy", "magia", "dragon", "epica",
               "mitolog")                                                  to BookBindingStyle.FANTASY,
        listOf("terror", "horror", "paranormal", "fantasma", "vampir",
               "sobrenatural", "ocultis")                                  to BookBindingStyle.PARANORMAL,
        listOf("romance", "romantic", "amor", "pasion")                    to BookBindingStyle.LOVE,
        listOf("guerra", "war", "belic", "militar", "batalla", "soldado")  to BookBindingStyle.WAR,
        listOf("humor", "comedia", "comic", "satira", "parodia")           to BookBindingStyle.COMEDY,
        listOf("negra", "noir", "policia", "detective", "crimen",
               "thriller", "suspens", "misterio", "intriga")               to BookBindingStyle.NOIR,
        listOf("ciencia", "psicolog", "filosof", "ensayo", "tecnic",
               "matemat", "fisica", "biolog", "medicina", "academ")        to BookBindingStyle.SCIENTIFIC,
        listOf("historia", "historic", "medieval", "biografia",
               "memorias", "cronica")                                      to BookBindingStyle.MEDIEVAL
    )

    /** Quita acentos y pasa a minúsculas para que "Fantasía" case con "fantasia". */
    private fun normalizar(s: String): String {
        val sinTildes = java.text.Normalizer.normalize(s, java.text.Normalizer.Form.NFD)
            .replace(Regex("\\p{Mn}+"), "")
        return sinTildes.lowercase()
    }

    /**
     * Marco que corresponde a un libro. La categoría manda; el título solo se
     * consulta si la categoría no dice nada útil ("General", "Novela", vacía),
     * para no dejar todo en Clásico cuando el catálogo no está bien etiquetado.
     */
    fun estiloPara(categoria: String?, titulo: String? = null): BookBindingStyle {
        val cat = normalizar(categoria.orEmpty())
        CLAVES.firstOrNull { (claves, _) -> claves.any { it in cat } }?.let { return it.second }

        val tit = normalizar(titulo.orEmpty())
        if (tit.isNotBlank()) {
            CLAVES.firstOrNull { (claves, _) -> claves.any { it in tit } }?.let { return it.second }
        }
        return BookBindingStyle.CLASSIC
    }

    fun estiloPara(book: Book): BookBindingStyle = estiloPara(book.category, book.title)

    /** Pista sugerida directamente desde el libro. */
    fun pistaSugerida(book: Book): MusicTrack? = pistaSugerida(estiloPara(book))
}
