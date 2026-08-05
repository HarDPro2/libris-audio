package com.librisaudio.app.data.model

data class MusicTrack(
    val id: String,
    val title: String,
    val composer: String,
    val category: String, // Piano, Cuerdas, Orquesta, Ambiente
    val streamUrl: String
)

object BackgroundMusicCatalog {
    val tracks = listOf(
        // Piano Clásico & Romántico
        MusicTrack("d1", "Clair de Lune", "Claude Debussy", "Piano", "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"),
        MusicTrack("b1", "Sonata Claro de Luna (Adagio)", "Ludwig van Beethoven", "Piano", "https://cdn.pixabay.com/download/audio/2022/03/10/audio_511c970404.mp3"),
        MusicTrack("c1", "Nocturno Op. 9 No. 2", "Frédéric Chopin", "Piano", "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c35f29910d.mp3"),
        MusicTrack("s1", "Gymnopédie No. 1", "Erik Satie", "Piano", "https://cdn.pixabay.com/download/audio/2021/08/09/audio_82c23769c0.mp3"),
        MusicTrack("b2", "Für Elise (Para Elisa)", "Ludwig van Beethoven", "Piano", "https://cdn.pixabay.com/download/audio/2022/10/25/audio_228c2c1920.mp3"),
        MusicTrack("c2", "Preludio Op. 28 No. 4", "Frédéric Chopin", "Piano", "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"),
        MusicTrack("c3", "Vals en La Menor", "Frédéric Chopin", "Piano", "https://cdn.pixabay.com/download/audio/2022/02/10/audio_e88b64e0aa.mp3"),
        MusicTrack("l1", "Liebestraum No. 3 (Sueño de Amor)", "Franz Liszt", "Piano", "https://cdn.pixabay.com/download/audio/2022/05/16/audio_03d987d692.mp3"),
        MusicTrack("d2", "Rêverie", "Claude Debussy", "Piano", "https://cdn.pixabay.com/download/audio/2022/03/24/audio_349d3edbf9.mp3"),
        MusicTrack("s2", "Gnossienne No. 1", "Erik Satie", "Piano", "https://cdn.pixabay.com/download/audio/2022/08/02/audio_88c42a2253.mp3"),

        // Cuerdas, Orquesta & Barroco
        MusicTrack("ba1", "Aria para la cuerda de Sol", "Johann Sebastian Bach", "Cuerdas", "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8e8c871fa1.mp3"),
        MusicTrack("ba2", "Suite para Cello No. 1 (Preludio)", "Johann Sebastian Bach", "Cuerdas", "https://cdn.pixabay.com/download/audio/2022/01/18/audio_27918a99d2.mp3"),
        MusicTrack("p1", "Canon en Re Mayor", "Johann Pachelbel", "Barroco", "https://cdn.pixabay.com/download/audio/2022/05/27/audio_c3c3a9ebec.mp3"),
        MusicTrack("v1", "Las 4 Estaciones - Invierno (Largo)", "Antonio Vivaldi", "Barroco", "https://cdn.pixabay.com/download/audio/2022/03/24/audio_145d2f62ad.mp3"),
        MusicTrack("v2", "Las 4 Estaciones - Primavera (Largo)", "Antonio Vivaldi", "Barroco", "https://cdn.pixabay.com/download/audio/2022/04/19/audio_13a17e0e7a.mp3"),
        MusicTrack("a1", "Adagio en Sol Menor", "Tomaso Albinoni", "Barroco", "https://cdn.pixabay.com/download/audio/2022/02/15/audio_73bb859a11.mp3"),
        MusicTrack("m1", "Concierto para Clarinete K. 622 (Adagio)", "Wolfgang Amadeus Mozart", "Orquesta", "https://cdn.pixabay.com/download/audio/2022/03/10/audio_f53535928b.mp3"),
        MusicTrack("m2", "Eine kleine Nachtmusik (Romanze)", "Wolfgang Amadeus Mozart", "Orquesta", "https://cdn.pixabay.com/download/audio/2022/01/26/audio_9242cfbd8a.mp3"),
        MusicTrack("t1", "El Lago de los Cisnes (Escena)", "Pyotr Ilyich Tchaikovsky", "Orquesta", "https://cdn.pixabay.com/download/audio/2022/05/03/audio_78b273299c.mp3"),
        MusicTrack("sc1", "Ave María", "Franz Schubert", "Cuerdas", "https://cdn.pixabay.com/download/audio/2022/03/15/audio_98555e107b.mp3"),

        // Ambiente & Naturaleza
        MusicTrack("n1", "Lluvia Suave en la Ventana", "Sonido Ambiente", "Ambiente", "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"),
        MusicTrack("n2", "Fuego de Chimenea Acogedor", "Sonido Ambiente", "Ambiente", "https://cdn.pixabay.com/download/audio/2022/03/24/audio_349d3edbf9.mp3"),
        MusicTrack("n3", "Noche de Bosque & Grillos", "Sonido Ambiente", "Ambiente", "https://cdn.pixabay.com/download/audio/2022/05/16/audio_03d987d692.mp3"),
        MusicTrack("n4", "Océano y Olas Suaves", "Sonido Ambiente", "Ambiente", "https://cdn.pixabay.com/download/audio/2022/08/02/audio_88c42a2253.mp3")
    )
}
