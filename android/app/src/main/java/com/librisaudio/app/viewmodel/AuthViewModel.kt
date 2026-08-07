package com.librisaudio.app.viewmodel

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librisaudio.app.data.api.AppwriteAuthClient
import com.librisaudio.app.data.api.AppwriteSdkClient
import com.librisaudio.app.data.model.AppwriteEmailLoginBody
import com.librisaudio.app.data.model.AppwriteRegisterBody
import com.librisaudio.app.data.model.AppwriteSession
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.util.UUID

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Authenticated(val session: AppwriteSession) : AuthState()
    object Unauthenticated : AuthState()
    data class Error(val message: String) : AuthState()
}

class AuthViewModel : ViewModel() {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState

    private lateinit var prefs: SharedPreferences

    fun init(context: Context) {
        prefs = context.getSharedPreferences("libris_prefs", Context.MODE_PRIVATE)
        val savedUserId  = prefs.getString("user_id", null)
        val savedEmail   = prefs.getString("user_email", null)
        val savedName    = prefs.getString("user_name", null)
        val savedSession = prefs.getString("session_id", null)

        if (savedUserId != null && savedEmail != null && savedSession != null) {
            _authState.value = AuthState.Authenticated(
                AppwriteSession(
                    userId    = savedUserId,
                    email     = savedEmail,
                    name      = savedName ?: savedEmail.substringBefore("@"),
                    sessionId = savedSession
                )
            )
        } else {
            _authState.value = AuthState.Unauthenticated
        }
    }

    fun login(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _authState.value = AuthState.Error("Por favor ingresa email y contraseña")
            return
        }
        _authState.value = AuthState.Loading

        viewModelScope.launch {
            try {
                Log.d("AuthViewModel", "Login: enviando a Appwrite")
                val sessionResp = AppwriteAuthClient.authService.loginWithEmail(
                    body = AppwriteEmailLoginBody(email = email.trim(), password = password)
                )
                Log.d("AuthViewModel", "Login: sesión obtenida id=${sessionResp.`$id`}")

                val cookieValue = "a_session_${AppwriteAuthClient.APPWRITE_PROJECT_ID}=${sessionResp.`$id`}"
                val userResp = AppwriteAuthClient.authService.getAccount(
                    cookieHeader = cookieValue
                )
                Log.d("AuthViewModel", "Login: cuenta obtenida userId=${userResp.`$id`} email=${userResp.email}")

                val session = AppwriteSession(
                    userId    = userResp.`$id`,
                    email     = userResp.email,
                    name      = userResp.name.ifBlank { userResp.email.substringBefore("@") },
                    sessionId = sessionResp.`$id`
                )
                saveSession(session)
                _authState.value = AuthState.Authenticated(session)
            } catch (e: HttpException) {
                val errorBody = parseAppwriteError(e)
                Log.e("AuthViewModel", "Login HttpException code=${e.code()} body=$errorBody")
                val msg = when (e.code()) {
                    401  -> "Email o contraseña incorrectos"
                    400  -> "Datos inválidos: $errorBody"
                    429  -> "Demasiados intentos. Espera un momento"
                    else -> "Error ${e.code()}: $errorBody"
                }
                _authState.value = AuthState.Error(msg)
            } catch (e: Exception) {
                Log.e("AuthViewModel", "Login error: ${e.javaClass.simpleName} — ${e.message}", e)
                val msg = when {
                    e.message?.contains("Unable to resolve host") == true -> "Sin conexión: no se puede alcanzar el servidor"
                    e.message?.contains("timeout") == true               -> "Tiempo de espera agotado. Revisa tu conexión"
                    e.message?.contains("SSL") == true                   -> "Error de certificado SSL"
                    else -> "Error de red: ${e.message ?: "desconocido"}"
                }
                _authState.value = AuthState.Error(msg)
            }
        }
    }

    fun register(name: String, email: String, password: String, confirmPassword: String) {
        when {
            name.isBlank() || email.isBlank() || password.isBlank() ->
                _authState.value = AuthState.Error("Todos los campos son obligatorios")
            !email.contains("@") || !email.contains(".") ->
                _authState.value = AuthState.Error("Ingresa un email válido (ej: usuario@gmail.com)")
            password != confirmPassword ->
                _authState.value = AuthState.Error("Las contraseñas no coinciden")
            password.length < 8 ->
                _authState.value = AuthState.Error("La contraseña debe tener al menos 8 caracteres")
            else -> {
                _authState.value = AuthState.Loading
                viewModelScope.launch {
                    try {
                        val userId = UUID.randomUUID().toString()
                        AppwriteAuthClient.authService.registerAccount(
                            body = AppwriteRegisterBody(
                                userId   = userId,
                                email    = email.trim(),
                                password = password,
                                name     = name.trim()
                            )
                        )
                        // Auto-login after successful registration
                        login(email.trim(), password)
                    } catch (e: HttpException) {
                        val errorBody = parseAppwriteError(e)
                        Log.e("AuthViewModel", "Registro HttpException code=${e.code()} body=$errorBody")
                        val msg = when (e.code()) {
                            409  -> "Ya existe una cuenta con ese email"
                            400  -> "Datos inválidos. Verifica el email y que la contraseña tenga al menos 8 caracteres"
                            429  -> "Demasiados intentos. Espera un momento"
                            else -> "Error al registrar (${e.code()}): $errorBody"
                        }
                        _authState.value = AuthState.Error(msg)
                    } catch (e: Exception) {
                        Log.e("AuthViewModel", "Registro error: ${e.javaClass.simpleName} — ${e.message}", e)
                        val msg = when {
                            e.message?.contains("Unable to resolve host") == true -> "Sin conexión al servidor"
                            e.message?.contains("timeout") == true               -> "Tiempo de espera agotado"
                            else -> "Error de red: ${e.message ?: "desconocido"}"
                        }
                        _authState.value = AuthState.Error(msg)
                    }
                }
            }
        }
    }

    /**
     * Called when the OAuth deep link returns to the app.
     * TOKEN flow: Appwrite redirects to
     *   appwrite-callback-{projectId}://?userId=X&secret=Y
     * We exchange (userId, secret) for a session via POST /v1/account/sessions/token,
     * then fetch the account with the resulting session cookie.
     */
    fun handleOAuthCallback(uri: android.net.Uri) {
        val allParams = uri.queryParameterNames.joinToString { "$it=${uri.getQueryParameter(it)}" }
        Log.d("AuthViewModel", "OAuth callback URI: $uri | params: $allParams")

        _authState.value = AuthState.Loading

        val userId = uri.getQueryParameter("userId") ?: ""
        val secret = uri.getQueryParameter("secret") ?: ""

        if (userId.isBlank() || secret.isBlank()) {
            // Empty callback = OAuth failed at Appwrite/Google level
            Log.e("AuthViewModel", "OAuth failed — no userId/secret. URI=$uri")
            _authState.value = AuthState.Error("Login con Google falló. Verifica la configuración del proveedor en Appwrite.")
            return
        }

        viewModelScope.launch {
            try {
                // 1. Exchange token for a real session
                Log.d("AuthViewModel", "Exchanging OAuth token for session...")
                val sessionResp = AppwriteAuthClient.authService.createSessionFromToken(
                    body = com.librisaudio.app.data.model.AppwriteTokenSessionBody(
                        userId = userId,
                        secret = secret
                    )
                )
                Log.d("AuthViewModel", "Session created id=${sessionResp.`$id`} hasSecret=${!sessionResp.secret.isNullOrBlank()}")

                // 2. Fetch account info with the session cookie.
                // The token flow returns a `secret` — that's the actual cookie value.
                val cookieToken = sessionResp.secret?.takeIf { it.isNotBlank() } ?: sessionResp.`$id`
                val cookieValue = "a_session_${AppwriteAuthClient.APPWRITE_PROJECT_ID}=${cookieToken}"
                val userResp = AppwriteAuthClient.authService.getAccount(cookieHeader = cookieValue)
                Log.d("AuthViewModel", "OAuth account OK: ${userResp.email}")

                val session = AppwriteSession(
                    userId    = userResp.`$id`,
                    email     = userResp.email,
                    name      = userResp.name.ifBlank { userResp.email.substringBefore("@") },
                    sessionId = cookieToken
                )
                saveSession(session)
                _authState.value = AuthState.Authenticated(session)
            } catch (e: HttpException) {
                val body = parseAppwriteError(e)
                Log.e("AuthViewModel", "OAuth token exchange failed ${e.code()}: $body")
                _authState.value = AuthState.Error("Error Google ${e.code()}: $body")
            } catch (e: Exception) {
                Log.e("AuthViewModel", "OAuth exception: ${e.message}", e)
                _authState.value = AuthState.Error("Error red OAuth: ${e.javaClass.simpleName}: ${e.message?.take(80)}")
            }
        }
    }

    fun logout() {
        val session = (_authState.value as? AuthState.Authenticated)?.session ?: return
        viewModelScope.launch {
            try {
                val cookieValue = "a_session_${AppwriteAuthClient.APPWRITE_PROJECT_ID}=${session.sessionId}"
                AppwriteAuthClient.authService.deleteSession(
                    cookieHeader  = cookieValue,
                    sessionIdPath = "current"
                )
            } catch (_: Exception) { /* ignora error de red en logout */ }
            clearSession()
            _authState.value = AuthState.Unauthenticated
        }
    }

    fun dismissError() {
        _authState.value = AuthState.Unauthenticated
    }

    private fun saveSession(session: AppwriteSession) {
        prefs.edit()
            .putString("user_id",    session.userId)
            .putString("user_email", session.email)
            .putString("user_name",  session.name)
            .putString("session_id", session.sessionId)
            .apply()
    }

    private fun clearSession() {
        prefs.edit().clear().apply()
    }

    private fun parseAppwriteError(e: HttpException): String {
        return try {
            e.response()?.errorBody()?.string()
                ?.let { body ->
                    val msgMatch = Regex("\"message\"\\s*:\\s*\"([^\"]+)\"").find(body)
                    msgMatch?.groupValues?.get(1) ?: body.take(120)
                } ?: "Error desconocido"
        } catch (_: Exception) { "Error desconocido" }
    }
}
