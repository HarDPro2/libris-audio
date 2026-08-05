package com.librisaudio.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Login
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.viewmodel.AuthState
import com.librisaudio.app.viewmodel.AuthViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(
    authViewModel: AuthViewModel,
    authState: AuthState,
    currentTheme: AppThemePreset
) {
    var isRegisterMode by remember { mutableStateOf(false) }

    // Form fields
    var name      by remember { mutableStateOf("") }
    var email     by remember { mutableStateOf("") }
    var password  by remember { mutableStateOf("") }
    var confirm   by remember { mutableStateOf("") }
    var showPass  by remember { mutableStateOf(false) }
    var showConf  by remember { mutableStateOf(false) }

    val focusManager = LocalFocusManager.current
    val isLoading = authState is AuthState.Loading

    // Theme gradient colors
    val gradientStart = currentTheme.primary.copy(alpha = 0.15f)
    val gradientEnd   = Color(0xFF0A0F1E)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    colors = listOf(gradientStart, gradientEnd),
                    center = Offset(0.5f, 0.2f),
                    radius = 1200f
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Spacer(modifier = Modifier.height(48.dp))

            // ── Logo / Brand ──────────────────────────────────────────────
            Icon(
                imageVector = Icons.Default.AutoStories,
                contentDescription = "Libris Audio",
                tint = currentTheme.primary,
                modifier = Modifier.size(64.dp)
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Libris Audio",
                fontSize = 30.sp,
                fontWeight = FontWeight.ExtraBold,
                color = Color.White,
                letterSpacing = 1.sp
            )

            Text(
                text = "Tu biblioteca de audiolibros con IA",
                fontSize = 13.sp,
                color = Color(0xFF8FA3BF),
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 4.dp, bottom = 32.dp)
            )

            // ── Toggle Login / Register ───────────────────────────────────
            Row(
                modifier = Modifier
                    .clip(RoundedCornerShape(14.dp))
                    .background(Color(0x22FFFFFF))
                    .padding(4.dp)
                    .fillMaxWidth(0.85f),
                horizontalArrangement = Arrangement.Center
            ) {
                listOf("Iniciar sesión" to false, "Crear cuenta" to true).forEach { (label, mode) ->
                    val selected = isRegisterMode == mode
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .background(if (selected) currentTheme.primary else Color.Transparent)
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        TextButton(onClick = {
                            isRegisterMode = mode
                            authViewModel.dismissError()
                        }) {
                            Text(
                                text = label,
                                color = if (selected) Color.White else Color(0xFF8FA3BF),
                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // ── Card with form ────────────────────────────────────────────
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                color = Color(0xCC1E293B),
                tonalElevation = 4.dp
            ) {
                Column(modifier = Modifier.padding(24.dp)) {

                    // Name field (register only)
                    AnimatedVisibility(
                        visible = isRegisterMode,
                        enter = expandVertically() + fadeIn(),
                        exit  = shrinkVertically() + fadeOut()
                    ) {
                        Column {
                            AuthTextField(
                                value         = name,
                                onValueChange = { name = it },
                                label         = "Nombre completo",
                                icon          = Icons.Default.Person,
                                imeAction     = ImeAction.Next,
                                keyboardType  = KeyboardType.Text,
                                onImeAction   = { focusManager.moveFocus(FocusDirection.Down) },
                                currentTheme  = currentTheme
                            )
                            Spacer(modifier = Modifier.height(14.dp))
                        }
                    }

                    // Email
                    AuthTextField(
                        value         = email,
                        onValueChange = { email = it },
                        label         = "Correo electrónico",
                        icon          = Icons.Default.Email,
                        imeAction     = ImeAction.Next,
                        keyboardType  = KeyboardType.Email,
                        onImeAction   = { focusManager.moveFocus(FocusDirection.Down) },
                        currentTheme  = currentTheme
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    // Password
                    AuthTextField(
                        value         = password,
                        onValueChange = { password = it },
                        label         = "Contraseña",
                        icon          = Icons.Default.Lock,
                        imeAction     = if (isRegisterMode) ImeAction.Next else ImeAction.Done,
                        keyboardType  = KeyboardType.Password,
                        isPassword    = true,
                        showPassword  = showPass,
                        onTogglePass  = { showPass = !showPass },
                        onImeAction   = {
                            if (isRegisterMode) focusManager.moveFocus(FocusDirection.Down)
                            else focusManager.clearFocus()
                        },
                        currentTheme  = currentTheme
                    )

                    // Confirm password (register only)
                    AnimatedVisibility(
                        visible = isRegisterMode,
                        enter = expandVertically() + fadeIn(),
                        exit  = shrinkVertically() + fadeOut()
                    ) {
                        Column {
                            Spacer(modifier = Modifier.height(14.dp))
                            AuthTextField(
                                value         = confirm,
                                onValueChange = { confirm = it },
                                label         = "Confirmar contraseña",
                                icon          = Icons.Default.LockOpen,
                                imeAction     = ImeAction.Done,
                                keyboardType  = KeyboardType.Password,
                                isPassword    = true,
                                showPassword  = showConf,
                                onTogglePass  = { showConf = !showConf },
                                onImeAction   = { focusManager.clearFocus() },
                                currentTheme  = currentTheme
                            )
                        }
                    }

                    // Error message
                    if (authState is AuthState.Error) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(10.dp))
                                .background(Color(0x33FF4444))
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Warning,
                                contentDescription = null,
                                tint = Color(0xFFFF6B6B),
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = authState.message,
                                color = Color(0xFFFF8F8F),
                                fontSize = 13.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // Submit button
                    Button(
                        onClick = {
                            focusManager.clearFocus()
                            if (isRegisterMode) {
                                authViewModel.register(name, email, password, confirm)
                            } else {
                                authViewModel.login(email, password)
                            }
                        },
                        enabled = !isLoading,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = currentTheme.primary,
                            disabledContainerColor = currentTheme.primary.copy(alpha = 0.5f)
                        )
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                color = Color.White,
                                modifier = Modifier.size(22.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(
                                imageVector = if (isRegisterMode) Icons.Default.PersonAdd else Login,
                                contentDescription = null,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = if (isRegisterMode) "Crear cuenta" else "Iniciar sesión",
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Footer note
            Text(
                text = "Tus datos se almacenan de forma segura en Appwrite Cloud.\nNunca compartimos tu información.",
                fontSize = 11.sp,
                color = Color(0xFF4A6080),
                textAlign = TextAlign.Center,
                lineHeight = 16.sp,
                modifier = Modifier.padding(horizontal = 16.dp)
            )

            Spacer(modifier = Modifier.height(48.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AuthTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    imeAction: ImeAction,
    keyboardType: KeyboardType,
    currentTheme: AppThemePreset,
    isPassword: Boolean = false,
    showPassword: Boolean = false,
    onTogglePass: (() -> Unit)? = null,
    onImeAction: () -> Unit = {}
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        leadingIcon = {
            Icon(icon, contentDescription = null, tint = currentTheme.primary.copy(alpha = 0.8f))
        },
        trailingIcon = if (isPassword) {
            {
                IconButton(onClick = { onTogglePass?.invoke() }) {
                    Icon(
                        imageVector = if (showPassword) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                        contentDescription = if (showPassword) "Ocultar" else "Mostrar",
                        tint = Color(0xFF8FA3BF)
                    )
                }
            }
        } else null,
        visualTransformation = if (isPassword && !showPassword) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(
            keyboardType = keyboardType,
            imeAction = imeAction
        ),
        keyboardActions = KeyboardActions(
            onNext = { onImeAction() },
            onDone = { onImeAction() }
        ),
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor   = currentTheme.primary,
            unfocusedBorderColor = Color(0x33FFFFFF),
            focusedLabelColor    = currentTheme.primary,
            unfocusedLabelColor  = Color(0xFF8FA3BF),
            focusedTextColor     = Color.White,
            unfocusedTextColor   = Color.White,
            cursorColor          = currentTheme.primary,
            focusedContainerColor   = Color(0x111E293B),
            unfocusedContainerColor = Color(0x111E293B)
        )
    )
}
