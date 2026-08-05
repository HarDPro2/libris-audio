package com.librisaudio.app.data.model

import com.google.gson.annotations.SerializedName

data class GlobalBookDto(
    @SerializedName("id") val id: String? = null,
    @SerializedName("book_id") val bookId: String? = null,
    @SerializedName("title") val title: String? = null,
    @SerializedName("author") val author: String? = null,
    @SerializedName("category") val category: String? = null,
    @SerializedName("cover_url") val coverUrl: String? = null,
    @SerializedName("parts_count") val partsCount: Int? = 1,
    @SerializedName("added_by") val addedBy: String? = null
)

data class UserBookDto(
    @SerializedName("id") val id: String,
    @SerializedName("book_id") val bookId: String,
    @SerializedName("current_part_index") val currentPartIndex: Int? = 0,
    @SerializedName("current_time") val currentTime: Double? = 0.0,
    @SerializedName("progress") val progress: Int? = 0,
    @SerializedName("global_books") val globalBook: GlobalBookDto? = null
)

data class Book(
    val id: String,
    val bookId: String,
    val title: String,
    val author: String = "Libris Audio",
    val category: String = "General",
    val coverUrl: String? = null,
    val partsCount: Int = 1,
    val currentPartIndex: Int = 0,
    val currentTimeSec: Double = 0.0,
    val progressPercent: Int = 0,
    val addedBy: String = ""
) {
    fun getAudioUrl(partIndex: Int = currentPartIndex, voice: String = "es-MX-JorgeNeural"): String {
        return "https://libris-audio-backend-856706599879.us-west1.run.app/api/audio/$bookId/$partIndex?voice=$voice"
    }
}

