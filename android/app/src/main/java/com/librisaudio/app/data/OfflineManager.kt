package com.librisaudio.app.data

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.librisaudio.app.data.api.ApiClient
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.data.model.WordTiming
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.util.concurrent.TimeUnit

/** Metadatos de un libro descargado para escuchar sin conexión. */
data class OfflineBook(
    val bookId: String,
    val title: String,
    val author: String,
    val coverUrl: String?,
    val category: String,
    val partsCount: Int,
    val voice: String,
    val complete: Boolean = false,
    val sizeBytes: Long = 0
)

/**
 * Descarga y gestiona libros offline (audio + texto + timing) en almacenamiento
 * interno: filesDir/offline/{bookId}/{audio|text|timing}/…  + meta.json.
 * La reproducción usa el archivo local si existe (fallback en PlayerViewModel).
 */
class OfflineManager(context: Context) {

    private val appCtx = context.applicationContext
    private val root = File(appCtx.filesDir, "offline")
    private val gson = Gson()
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)   // la generación TTS puede tardar
        .build()

    private fun sanitize(s: String) = s.replace(Regex("[^A-Za-z0-9._-]"), "_")
    private fun bookDir(bookId: String) = File(root, sanitize(bookId))
    private fun audioFileFor(bookId: String, part: Int, voice: String) =
        File(bookDir(bookId), "audio/part_${part}_${sanitize(voice)}.mp3")
    private fun textFileFor(bookId: String, part: Int) =
        File(bookDir(bookId), "text/part_$part.txt")
    private fun timingFileFor(bookId: String, part: Int, voice: String) =
        File(bookDir(bookId), "timing/part_${part}_${sanitize(voice)}.json")
    private fun metaFileFor(bookId: String) = File(bookDir(bookId), "meta.json")

    // ── Consultas (para reproducción y UI) ──────────────────────────────────
    fun isDownloaded(bookId: String): Boolean = metaFileFor(bookId).exists()

    fun localAudio(bookId: String, part: Int, voice: String): File? =
        audioFileFor(bookId, part, voice).takeIf { it.exists() && it.length() > 0 }

    fun localText(bookId: String, part: Int): String? =
        textFileFor(bookId, part).takeIf { it.exists() }?.readText(Charsets.UTF_8)

    fun localTimings(bookId: String, part: Int, voice: String): List<WordTiming>? {
        val f = timingFileFor(bookId, part, voice).takeIf { it.exists() } ?: return null
        return try {
            val type = object : TypeToken<List<WordTiming>>() {}.type
            gson.fromJson(f.readText(Charsets.UTF_8), type)
        } catch (_: Exception) { null }
    }

    fun downloadedBooks(): List<OfflineBook> {
        val dirs = root.listFiles()?.filter { it.isDirectory } ?: return emptyList()
        return dirs.mapNotNull { d ->
            val meta = File(d, "meta.json").takeIf { it.exists() } ?: return@mapNotNull null
            try {
                gson.fromJson(meta.readText(), OfflineBook::class.java)?.copy(sizeBytes = dirSize(d))
            } catch (_: Exception) { null }
        }.sortedBy { it.title.lowercase() }
    }

    fun totalSizeBytes(): Long = if (root.exists()) dirSize(root) else 0L

    // ── Descarga ────────────────────────────────────────────────────────────
    /**
     * Descarga TODAS las partes (audio imprescindible; texto y timing best-effort)
     * del libro para [voice]. onProgress(done, total). Devuelve true si el audio
     * quedó completo en todas las partes.
     */
    suspend fun download(book: Book, voice: String, onProgress: (Int, Int) -> Unit): Boolean =
        withContext(Dispatchers.IO) {
            val total = book.partsCount.coerceAtLeast(1)
            bookDir(book.bookId).apply {
                File(this, "audio").mkdirs()
                File(this, "text").mkdirs()
                File(this, "timing").mkdirs()
            }
            var audioOk = 0
            for (i in 0 until total) {
                val aFile = audioFileFor(book.bookId, i, voice)
                if (aFile.exists() && aFile.length() > 0) audioOk++
                else if (downloadTo(book.getAudioUrl(i, voice), aFile)) audioOk++

                val tFile = textFileFor(book.bookId, i)
                if (!tFile.exists())
                    downloadTo("${ApiClient.BACKEND_URL}api/text/${book.bookId}/$i", tFile)

                val gFile = timingFileFor(book.bookId, i, voice)
                if (!gFile.exists())
                    downloadTo("${ApiClient.BACKEND_URL}api/timing/${book.bookId}/$i?voice=$voice", gFile)

                onProgress(i + 1, total)
            }
            val complete = audioOk == total
            if (audioOk > 0) writeMeta(book, voice, complete)
            complete
        }

    private fun writeMeta(book: Book, voice: String, complete: Boolean) {
        val meta = OfflineBook(
            bookId = book.bookId, title = book.title, author = book.author,
            coverUrl = book.coverUrl, category = book.category,
            partsCount = book.partsCount, voice = voice, complete = complete
        )
        metaFileFor(book.bookId).writeText(gson.toJson(meta))
    }

    private fun downloadTo(url: String, dest: File): Boolean = try {
        client.newCall(Request.Builder().url(url).build()).execute().use { res ->
            if (!res.isSuccessful) return false
            val body = res.body ?: return false
            dest.parentFile?.mkdirs()
            dest.outputStream().use { out -> body.byteStream().copyTo(out) }
            dest.length() > 0
        }
    } catch (_: Exception) { false }

    // ── Borrado ─────────────────────────────────────────────────────────────
    fun delete(bookId: String) { bookDir(bookId).deleteRecursively() }
    fun deleteAll() { root.deleteRecursively() }

    private fun dirSize(dir: File): Long =
        dir.walkTopDown().filter { it.isFile }.sumOf { it.length() }
}
