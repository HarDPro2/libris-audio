package com.librisaudio.app.data.api

import android.content.Context
import io.appwrite.Client
import io.appwrite.services.Account

/**
 * Wrapper around the official Appwrite Android SDK.
 * Used for:
 *  - Google OAuth (createOAuth2Session) — handles the session cookie automatically
 *  - Fetching the current account after OAuth redirect
 *
 * Email/password login + register still uses Retrofit (AppwriteAuthClient)
 * because the SDK's coroutine model requires an Activity reference for OAuth,
 * which we manage manually here.
 */
object AppwriteSdkClient {

    private var _client: Client? = null
    private var _account: Account? = null

    fun init(context: Context) {
        if (_client != null) return
        _client = Client(context)
            .setEndpoint(AppwriteAuthClient.APPWRITE_ENDPOINT.trimEnd('/'))
            .setProject(AppwriteAuthClient.APPWRITE_PROJECT_ID)
            .setSelfSigned(false)
        _account = Account(_client!!)
    }

    val account: Account
        get() = _account ?: error("AppwriteSdkClient not initialized — call init(context) first")

    val client: Client
        get() = _client ?: error("AppwriteSdkClient not initialized — call init(context) first")
}
