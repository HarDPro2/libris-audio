package com.librisaudio.app.data.model

data class MusicTrack(
    val id: String,
    val title: String,
    val composer: String,
    val category: String,
    val streamUrl: String
)

object BackgroundMusicCatalog {
    // GENERADO por backend/subir_musica.py — no editar a mano salvo para
    // corregir títulos o compositores. Todas las pistas existen en R2.
    private const val R2 = "https://pub-7ed2f9cce2d84ce5a6891e1e42008170.r2.dev/music"

    val tracks = listOf(
        MusicTrack("m1", "Arabesque no. 1 (string quartet arr.)", "Claude Debussy", "Clasica", "${R2}/clasica/arabesque_no_1_string_quartet_arr.mp3"),
        MusicTrack("m2", "Arabesque No. 1. Andantino con moto", "Claude Debussy", "Clasica", "${R2}/clasica/arabesque_no_1_andantino_con_moto.mp3"),
        MusicTrack("m3", "Nocturne in B flat minor, Op. 9 no. 1", "Frédéric Chopin", "Clasica", "${R2}/clasica/nocturne_in_b_flat_minor_op_9_no_1.mp3"),
        MusicTrack("m4", "Nocturne in D flat major, Op. 27 no. 2", "Frédéric Chopin", "Clasica", "${R2}/clasica/nocturne_in_d_flat_major_op_27_no_2.mp3"),
        MusicTrack("m5", "Nocturne in E flat major, Op. 9 no. 2", "Frédéric Chopin", "Clasica", "${R2}/clasica/nocturne_in_e_flat_major_op_9_no_2.mp3"),
        MusicTrack("m6", "Nocturne in F minor, Op. 55 no. 1", "Frédéric Chopin", "Clasica", "${R2}/clasica/nocturne_in_f_minor_op_55_no_1.mp3"),
        MusicTrack("m7", "Nocturnes, Op. 32 - No. 2. Nocturne in A♭ major", "Frédéric Chopin", "Clasica", "${R2}/clasica/nocturnes_op_32_no_2_nocturne_in_ab_major.mp3"),
        MusicTrack("m8", "Moonlight Sonata Op. 27 No. 2 - II. Allegretto", "Ludwig van Beethoven", "Clasica", "${R2}/clasica/paul_pitman_moonlight_sonata_op_27_no_2_ii_allegretto.mp3"),
        MusicTrack("m9", "Piano Sonata no. 14 in C#m 'Moonlight', Op. 27 no. 2 - I. Adagio sostenuto", "Ludwig van Beethoven", "Clasica", "${R2}/clasica/piano_sonata_no_14_in_csm_moonlight_op_27_no_2_i_adagio_sostenuto.mp3"),
        MusicTrack("m10", "Romance De Juegos Prohibidos", "Anónimo (atrib. Rubira)", "Clasica", "${R2}/clasica/romance_de_juegos_prohibidos.mp3"),
        MusicTrack("m11", "Santa Lucia", "Teodoro Cottrau", "Clasica", "${R2}/clasica/santa_lucia.mp3"),
        MusicTrack("m12", "Violin Concerto in D major, Op. 61 - III. Rondo_ Allegro", "Ludwig van Beethoven", "Clasica", "${R2}/clasica/violin_concerto_in_d_major_op_61_iii_rondo_allegro.mp3"),
        MusicTrack("m13", "Violin Concerto in D, Op. 61 - I. Allegro ma non troppo", "Ludwig van Beethoven", "Clasica", "${R2}/clasica/violin_concerto_in_d_op_61_i_allegro_ma_non_troppo.mp3"),
        MusicTrack("m14", "Violin Partita no. 2, BWV 1004 - 4. Giga", "Johann Sebastian Bach", "Clasica", "${R2}/clasica/violin_partita_no_2_bwv_1004_4_giga_guitar_arrangement.mp3"),
        MusicTrack("m15", "Violin Partita no. 2, BWV 1004", "Johann Sebastian Bach", "Clasica", "${R2}/clasica/violin_partita_no_2_bwv_1004.mp3")
    )

    val categorias: List<String> = tracks.map { it.category }.distinct()
}
