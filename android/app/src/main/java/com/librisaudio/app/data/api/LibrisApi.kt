package com.librisaudio.app.data.api

import com.librisaudio.app.data.model.GlobalBookDto
import com.librisaudio.app.data.model.UserBookDto
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface LibrisApiService {

    @GET("api/books")
    suspend fun getBooksFromBackend(): List<GlobalBookDto>

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
        @Part("added_by") addedBy: RequestBody
    ): Response<UploadResponse>
}

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
