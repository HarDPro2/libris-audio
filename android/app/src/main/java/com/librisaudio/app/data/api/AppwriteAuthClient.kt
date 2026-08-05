package com.librisaudio.app.data.api

import com.librisaudio.app.data.model.AppwriteSessionResponse
import com.librisaudio.app.data.model.AppwriteUserResponse
import com.librisaudio.app.data.model.AppwriteEmailLoginBody
import com.librisaudio.app.data.model.AppwriteRegisterBody
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import java.util.concurrent.TimeUnit

interface AppwriteAuthService {

    @POST("v1/account/sessions/email")
    suspend fun loginWithEmail(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("X-Appwrite-Response-Format") format: String = "1.6.0",
        @Header("Content-Type") contentType: String = "application/json",
        @Body body: AppwriteEmailLoginBody
    ): AppwriteSessionResponse

    @POST("v1/account")
    suspend fun registerAccount(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("X-Appwrite-Response-Format") format: String = "1.6.0",
        @Header("Content-Type") contentType: String = "application/json",
        @Body body: AppwriteRegisterBody
    ): AppwriteUserResponse

    @GET("v1/account")
    suspend fun getAccount(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("X-Appwrite-Session") sessionId: String,
        @Header("X-Appwrite-Response-Format") format: String = "1.6.0"
    ): AppwriteUserResponse

    @DELETE("v1/account/sessions/{sessionId}")
    suspend fun deleteSession(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("X-Appwrite-Session") sessionId: String,
        @Path("sessionId") sessionIdPath: String
    ): Unit
}

object AppwriteAuthClient {
    const val APPWRITE_ENDPOINT = "https://nyc.cloud.appwrite.io/"
    const val APPWRITE_PROJECT_ID = "6a72f5d6002eeff78bc2"

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()

    val authService: AppwriteAuthService by lazy {
        Retrofit.Builder()
            .baseUrl(APPWRITE_ENDPOINT)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(AppwriteAuthService::class.java)
    }
}
