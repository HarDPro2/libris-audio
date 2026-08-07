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
    // Solo las pistas REALES subidas a Cloudflare R2 (dominio público, Musopen).
    // Cada URL corresponde a un archivo que existe en el bucket.
    // Para añadir más: sube el MP3 a R2 y agrega su entrada aquí.
    // ─────────────────────────────────────────────────────────────────────
    private const val R2 = "https://pub-7ed2f9cce2d84ce5a6891e1e42008170.r2.dev/music"

    val tracks = listOf(
        MusicTrack("m1", "Sonata Claro de Luna (Adagio)", "Ludwig van Beethoven", "Piano",   "${"$"}{R2}/piano/sonata_luna_adagio.mp3"),
        MusicTrack("m2", "Sonata Claro de Luna II",       "Ludwig van Beethoven", "Piano",   "${"$"}{R2}/piano/fur_elise.mp3"),
        MusicTrack("m3", "Sonata Fácil K. 545 (Andante)", "Wolfgang A. Mozart",   "Piano",   "${"$"}{R2}/piano/preludio_op28_no4.mp3"),
        MusicTrack("m4", "Marcha Turca (K. 331)",         "Wolfgang A. Mozart",   "Piano",   "${"$"}{R2}/piano/vals_la_menor.mp3"),
        MusicTrack("m5", "Concierto para 2 Violines (BWV 1043)", "J. S. Bach",    "Cuerdas", "${"$"}{R2}/cuerdas/aria_cuerda_sol.mp3")
    )
}
