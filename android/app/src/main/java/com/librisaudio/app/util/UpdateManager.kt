package com.librisaudio.app.util

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * Auto-actualizador. Consulta el último release de GitHub, compara la versión
 * con la instalada (BuildConfig.VERSION_NAME) y, si hay una nueva, descarga el
 * APK (nombre fijo) y lanza el instalador del sistema vía FileProvider.
 */
object UpdateManager {

    private const val OWNER = "HarDPro2"
    private const val REPO  = "libris-audio"
    private const val LATEST_API = "https://api.github.com/repos/$OWNER/$REPO/releases/latest"
    // El asset tiene nombre FIJO (lo publica el CI), así el enlace nunca se rompe.
    const val APK_URL = "https://github.com/$OWNER/$REPO/releases/latest/download/libris-audio.apk"

    private val client = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .build()

    data class UpdateInfo(val versionName: String, val notes: String)

    /**
     * Devuelve UpdateInfo si el release remoto es MÁS NUEVO que [currentVersion],
     * o null si ya está al día / no se pudo consultar.
     */
    suspend fun checkForUpdate(currentVersion: String): UpdateInfo? = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder()
                .url(LATEST_API)
                .header("Accept", "application/vnd.github+json")
                .build()
            client.newCall(req).execute().use { res ->
                if (!res.isSuccessful) return@withContext null
                val body = res.body?.string() ?: return@withContext null
                val json = JSONObject(body)
                val tag = json.optString("tag_name").ifBlank { return@withContext null }
                val remote = tag.trimStart('v', 'V').trim()
                val notes = json.optString("body").take(500)
                if (isNewer(remote, currentVersion)) UpdateInfo(remote, notes) else null
            }
        } catch (_: Exception) {
            null
        }
    }

    /** Compara versiones semánticas simples ("1.0.10" > "1.0.9"). */
    fun isNewer(remote: String, local: String): Boolean {
        val r = remote.split(".").mapNotNull { it.filter(Char::isDigit).toIntOrNull() }
        val l = local.split(".").mapNotNull { it.filter(Char::isDigit).toIntOrNull() }
        val n = maxOf(r.size, l.size)
        for (i in 0 until n) {
            val a = r.getOrElse(i) { 0 }
            val b = l.getOrElse(i) { 0 }
            if (a != b) return a > b
        }
        return false
    }

    /**
     * Descarga el APK al caché interno. [onProgress] recibe 0..100 (o -1 si el
     * servidor no da tamaño). Devuelve el archivo o null si falla.
     */
    suspend fun downloadApk(context: Context, onProgress: (Int) -> Unit): File? =
        withContext(Dispatchers.IO) {
            try {
                val req = Request.Builder().url(APK_URL).build()
                client.newCall(req).execute().use { res ->
                    if (!res.isSuccessful) return@withContext null
                    val bodyStream = res.body?.byteStream() ?: return@withContext null
                    val total = res.body?.contentLength() ?: -1L
                    val outFile = File(context.cacheDir, "libris-update.apk")
                    if (outFile.exists()) outFile.delete()
                    outFile.outputStream().use { out ->
                        val buffer = ByteArray(8 * 1024)
                        var read: Int
                        var downloaded = 0L
                        while (bodyStream.read(buffer).also { read = it } != -1) {
                            out.write(buffer, 0, read)
                            downloaded += read
                            if (total > 0) onProgress(((downloaded * 100) / total).toInt())
                            else onProgress(-1)
                        }
                        out.flush()
                    }
                    outFile
                }
            } catch (_: Exception) {
                null
            }
        }

    /** Lanza el instalador del sistema para el APK descargado. */
    fun installApk(context: Context, apk: File) {
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", apk)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
    }
}
