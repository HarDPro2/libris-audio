package com.librisaudio.app.data.api

import com.librisaudio.app.data.model.GlobalBookDto
import com.librisaudio.app.data.model.UserBookDto
import com.librisaudio.app.data.model.UserStateDto
import com.librisaudio.app.data.model.WordTiming
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface LibrisApiService {

    @GET("api/books")
    suspend fun getBooksFromBackend(): List<GlobalBookDto>

    /** Devuelve el texto plano de una parte del libro para el modo Libro 3D. */
    @GET("api/text/{bookId}/{partIndex}")
    suspend fun getBookText(
        @Path("bookId") bookId: String,
        @Path("partIndex") partIndex: Int
    ): ResponseBody

    /** Tiempos de cada palabra para el resaltado sincronizado (karaoke). */
    @GET("api/timing/{bookId}/{partIndex}")
    suspend fun getTiming(
        @Path("bookId") bookId: String,
        @Path("partIndex") partIndex: Int,
        @Query("voice") voice: String
    ): List<WordTiming>

    /** Estado del usuario en la nube (progreso + preferencias). */
    @GET("api/user-state/{userId}")
    suspend fun getUserState(@Path("userId") userId: String): UserStateDto

    @PUT("api/user-state/{userId}")
    suspend fun putUserState(
        @Path("userId") userId: String,
        @Body body: UserStateDto
    ): ResponseBody

    /** Quita el libro del historial del usuario. No borra contenido. */
    @DELETE("api/library/{bookId}")
    suspend fun removeFromLibrary(
        @Path("bookId") bookId: String,
        @Header("Authorization") authorization: String
    ): Response<Unit>

    @DELETE("api/books/{bookId}")
    suspend fun deleteBook(
        @Path("bookId") bookId: String,
        @Header("Authorization") authorization: String
    ): Response<Unit>

    @PATCH("api/books/{bookId}")
    suspend fun patchBook(
        @Path("bookId") bookId: String,
        @Header("Authorization") authorization: String,
        @Body body: Map<String, String>
    ): Response<Unit>

    @Multipart
    @POST("api/upload-pdf")
    suspend fun uploadPdf(
        @Part file: MultipartBody.Part,
        @Part("title") title: RequestBody,
        @Part("category") category: RequestBody,
        @Part("added_by") addedBy: RequestBody,
        // El backend deriva el propietario de este token, no del campo
        // added_by (que era falsificable). Sin cabecera, responde 401.
        @Header("Authorization") authorization: String
    ): Response<UploadResponse>

    /** Asistente de voz A2: interpreta lenguaje natural → acción. */
    @POST("api/voice-command")
    suspend fun voiceCommand(@Body req: VoiceCommandRequest): VoiceCommandResponse
}

data class VoiceCommandRequest(
    val transcript: String,
    val current_part: Int,
    val parts_count: Int,
    val user_openrouter_key: String? = null,
    val enforce_free_only: Boolean = true
)

data class VoiceCommandResponse(
    val action: String = "unknown",
    val seconds: Int? = null,
    val part: Int? = null
)

data class UploadResponse(
    val title: String?,
    val bookId: String?,
    val partsCount: Int?,
    val coverUrl: String?
)

object ApiClient {
    const val BACKEND_URL = "https://libris-audio-backend-856706599879.us-west1.run.app/"

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()

    val backendService: LibrisApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BACKEND_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(LibrisApiService::class.java)
    }
}
