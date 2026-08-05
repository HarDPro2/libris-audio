package com.librisaudio.app.viewmodel

import android.content.Context
import android.content.SharedPreferences
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librisaudio.app.data.api.AppwriteAuthClient
import com.librisaudio.app.data.model.AppwriteEmailLoginBody
import com.librisaudio.app.data.model.AppwriteRegisterBody
import com.librisaudio.app.data.model.AppwriteSession
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

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
        // Check if we have a saved session
        val savedUserId   = prefs.getString("user_id", null)
        val savedEmail    = prefs.getString("user_email", null)
        val savedName     = prefs.getString("user_name", null)
        val savedSession  = prefs.getString("session_id", null)

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
                val sessionResp = AppwriteAuthClient.authService.loginWithEmail(
                    projectId = AppwriteAuthClient.APPWRITE_PROJECT_ID,
                    body = AppwriteEmailLoginBody(email = email.trim(), password = password)
                )
                // Fetch user info using the session
                val userResp = AppwriteAuthClient.authService.getAccount(
                    projectId = AppwriteAuthClient.APPWRITE_PROJECT_ID,
                    sessionId = sessionResp.`$id`
                )
                val session = AppwriteSession(
                    userId    = userResp.`$id`,
                    email     = userResp.email,
                    name      = userResp.name.ifBlank { userResp.email.substringBefore("@") },
                    sessionId = sessionResp.`$id`
                )
                saveSession(session)
                _authState.value = AuthState.Authenticated(session)
            } catch (e: Exception) {
                val msg = when {
                    e.message?.contains("401") == true -> "Email o contraseña incorrectos"
                    e.message?.contains("network") == true -> "Sin conexión a internet"
                    else -> "Error al iniciar sesión: ${e.message?.take(80)}"
                }
                _authState.value = AuthState.Error(msg)
            }
        }
    }

    fun register(name: String, email: String, password: String, confirmPassword: String) {
        when {
            name.isBlank() || email.isBlank() || password.isBlank() ->
                _authState.value = AuthState.Error("Todos los campos son obligatorios")
            password != confirmPassword ->
                _authState.value = AuthState.Error("Las contraseñas no coinciden")
            password.length < 8 ->
                _authState.value = AuthState.Error("La contraseña debe tener al menos 8 caracteres")
            else -> {
                _authState.value = AuthState.Loading
                viewModelScope.launch {
                    try {
                        // Appwrite requires a unique userId — use email-based slug
                        val userId = email.trim()
                            .substringBefore("@")
                            .replace(Regex("[^a-zA-Z0-9._-]"), "_")
                            .take(36)
                            .plus("_${System.currentTimeMillis() % 10000}")

                        AppwriteAuthClient.authService.registerAccount(
                            projectId = AppwriteAuthClient.APPWRITE_PROJECT_ID,
                            body = AppwriteRegisterBody(
                                userId   = userId,
                                email    = email.trim(),
                                password = password,
                                name     = name.trim()
                            )
                        )
                        // Auto-login after register
                        login(email, password)
                    } catch (e: Exception) {
                        val msg = when {
                            e.message?.contains("409") == true -> "Ya existe una cuenta con ese email"
                            e.message?.contains("400") == true -> "Email o contraseña inválidos"
                            else -> "Error al registrar: ${e.message?.take(80)}"
                        }
                        _authState.value = AuthState.Error(msg)
                    }
                }
            }
        }
    }

    fun logout() {
        val session = (_authState.value as? AuthState.Authenticated)?.session ?: return
        viewModelScope.launch {
            try {
                AppwriteAuthClient.authService.deleteSession(
                    projectId    = AppwriteAuthClient.APPWRITE_PROJECT_ID,
                    sessionId    = session.sessionId,
                    sessionIdPath = session.sessionId
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
}
