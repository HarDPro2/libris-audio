package com.librisaudio.app.data.model

data class MusicTrack(
    val id: String,
    val title: String,
    val composer: String,
    val category: String, // Piano, Cuerdas, Orquesta, Ambiente
    val streamUrl: String
)

object BackgroundMusicCatalog {
    // ─────────────────────────────────────────────────────────────────────
    // URLs apuntan a Cloudflare R2. Descarga las pistas desde Musopen.org
    // (dominio público, sin restricciones comerciales) y súbelas a R2 en:
    //   music/piano/clair_de_lune.mp3
    //   music/piano/sonata_luna.mp3   ... etc.
    // ─────────────────────────────────────────────────────────────────────
    private const val R2 = "https://pub-7ed2f9cce2d84ce5a6891e1e42008170.r2.dev/music"

    val tracks = listOf(
        // Piano Clásico & Romántico
        MusicTrack("d1",  "Clair de Lune",                  "Claude Debussy",        "Piano",    "${"$"}{R2}/piano/clair_de_lune.mp3"),
        MusicTrack("b1",  "Sonata Claro de Luna (Adagio)",   "Ludwig van Beethoven",  "Piano",    "${"$"}{R2}/piano/sonata_luna_adagio.mp3"),
        MusicTrack("c1",  "Nocturno Op. 9 No. 2",            "Frédéric Chopin",       "Piano",    "${"$"}{R2}/piano/nocturno_op9_no2.mp3"),
        MusicTrack("s1",  "Gymnopédie No. 1",                "Erik Satie",            "Piano",    "${"$"}{R2}/piano/gymnopedie_no1.mp3"),
        MusicTrack("b2",  "Für Elise",                       "Ludwig van Beethoven",  "Piano",    "${"$"}{R2}/piano/fur_elise.mp3"),
        MusicTrack("c2",  "Preludio Op. 28 No. 4",           "Frédéric Chopin",       "Piano",    "${"$"}{R2}/piano/preludio_op28_no4.mp3"),
        MusicTrack("c3",  "Vals en La Menor",                "Frédéric Chopin",       "Piano",    "${"$"}{R2}/piano/vals_la_menor.mp3"),
        MusicTrack("l1",  "Liebestraum No. 3 (Sueño de Amor)", "Franz Liszt",         "Piano",    "${"$"}{R2}/piano/liebestraum_no3.mp3"),
        MusicTrack("d2",  "Rêverie",                         "Claude Debussy",        "Piano",    "${"$"}{R2}/piano/reverie.mp3"),
        MusicTrack("s2",  "Gnossienne No. 1",                "Erik Satie",            "Piano",    "${"$"}{R2}/piano/gnossienne_no1.mp3"),

        // Cuerdas, Orquesta & Barroco
        MusicTrack("ba1", "Aria para la cuerda de Sol",      "Johann Sebastian Bach", "Cuerdas",  "${"$"}{R2}/cuerdas/aria_cuerda_sol.mp3"),
        MusicTrack("ba2", "Suite para Cello No. 1 (Preludio)","Johann Sebastian Bach","Cuerdas",  "${"$"}{R2}/cuerdas/suite_cello_no1.mp3"),
        MusicTrack("p1",  "Canon en Re Mayor",               "Johann Pachelbel",      "Barroco",  "${"$"}{R2}/barroco/canon_re_mayor.mp3"),
        MusicTrack("v1",  "Las 4 Estaciones - Invierno",     "Antonio Vivaldi",       "Barroco",  "${"$"}{R2}/barroco/cuatro_estaciones_invierno.mp3"),
        MusicTrack("v2",  "Las 4 Estaciones - Primavera",    "Antonio Vivaldi",       "Barroco",  "${"$"}{R2}/barroco/cuatro_estaciones_primavera.mp3"),
        MusicTrack("a1",  "Adagio en Sol Menor",             "Tomaso Albinoni",       "Barroco",  "${"$"}{R2}/barroco/adagio_sol_menor.mp3"),
        MusicTrack("m1",  "Concierto para Clarinete K. 622 (Adagio)", "Wolfgang Amadeus Mozart", "Orquesta", "${"$"}{R2}/orquesta/concierto_clarinete_adagio.mp3"),
        MusicTrack("m2",  "Eine kleine Nachtmusik (Romanze)","Wolfgang Amadeus Mozart","Orquesta", "${"$"}{R2}/orquesta/kleine_nachtmusik_romanze.mp3"),
        MusicTrack("t1",  "El Lago de los Cisnes (Escena)",  "Pyotr Ilyich Tchaikovsky","Orquesta","${"$"}{R2}/orquesta/lago_cisnes.mp3"),
        MusicTrack("sc1", "Ave María",                       "Franz Schubert",        "Cuerdas",  "${"$"}{R2}/cuerdas/ave_maria_schubert.mp3"),

        // Ambiente & Naturaleza
        MusicTrack("n1",  "Lluvia Suave en la Ventana",      "Sonido Ambiente",       "Ambiente", "${"$"}{R2}/ambiente/lluvia_suave.mp3"),
        MusicTrack("n2",  "Fuego de Chimenea Acogedor",      "Sonido Ambiente",       "Ambiente", "${"$"}{R2}/ambiente/chimenea.mp3"),
        MusicTrack("n3",  "Noche de Bosque & Grillos",       "Sonido Ambiente",       "Ambiente", "${"$"}{R2}/ambiente/bosque_noche.mp3"),
        MusicTrack("n4",  "Océano y Olas Suaves",            "Sonido Ambiente",       "Ambiente", "${"$"}{R2}/ambiente/oceano_olas.mp3")
    )
}
