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

    // Login with email+password — returns session
    @POST("v1/account/sessions/email")
    suspend fun loginWithEmail(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body body: AppwriteEmailLoginBody
    ): AppwriteSessionResponse

    // Register new account
    @POST("v1/account")
    suspend fun registerAccount(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body body: AppwriteRegisterBody
    ): AppwriteUserResponse

    // Get current account info — requires session cookie
    @GET("v1/account")
    suspend fun getAccount(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("Cookie") cookieHeader: String
    ): AppwriteUserResponse

    // Delete session (logout) — use "current" as sessionId path
    @DELETE("v1/account/sessions/{sessionId}")
    suspend fun deleteSession(
        @Header("X-Appwrite-Project") projectId: String,
        @Header("Cookie") cookieHeader: String,
        @Path("sessionId") sessionIdPath: String
    )
}

object AppwriteAuthClient {
    const val APPWRITE_ENDPOINT   = "https://nyc.cloud.appwrite.io/"
    const val APPWRITE_PROJECT_ID = "6a72f5d6002eeff78bc2"

    // Google OAuth URL — opens in browser, redirects back via deep link
    fun googleOAuthUrl(): String =
        "${APPWRITE_ENDPOINT}v1/account/sessions/oauth2/google" +
        "?project=${APPWRITE_PROJECT_ID}" +
        "&success=librisaudio://oauth/success" +
        "&failure=librisaudio://oauth/failure"

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
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
