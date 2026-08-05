package com.librisaudio.app.data.api

import com.librisaudio.app.data.model.GlobalBookDto
import com.librisaudio.app.data.model.UserBookDto
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface LibrisApiService {
    @GET("rest/v1/global_books")
    suspend fun getGlobalBooks(
        @Header("apikey") apiKey: String,
        @Query("select") select: String = "*"
    ): List<GlobalBookDto>

    @GET("rest/v1/user_books")
    suspend fun getUserBooks(
        @Header("apikey") apiKey: String,
        @Query("select") select: String = "*,global_books(*)"
    ): List<UserBookDto>
}

object ApiClient {
    private const val SUPABASE_URL = "https://ltyjvsenislyykjspjfb.supabase.co/"
    const val SUPABASE_ANON_KEY = "sb_publishable_4Ls4KIWHnQ-Hxa2G-dWQ2g_Z_PbilzO"
    const val BACKEND_URL = "https://libris-audio-backend-856706599879.us-west1.run.app/"

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()

    val supabaseService: LibrisApiService by lazy {
        Retrofit.Builder()
            .baseUrl(SUPABASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(LibrisApiService::class.java)
    }
}
