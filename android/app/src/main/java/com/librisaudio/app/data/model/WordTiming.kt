package com.librisaudio.app.data.model

/** Tiempo de una palabra: inicio (s) y fin (e) en milisegundos dentro de la parte. */
data class WordTiming(
    val w: String,
    val s: Long,
    val e: Long
)
