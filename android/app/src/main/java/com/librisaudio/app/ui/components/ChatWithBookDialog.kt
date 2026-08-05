package com.librisaudio.app.ui.components

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

data class ChatBubble(
    val id: String,
    val sender: String, // "user" or "ai"
    val text: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatWithBookDialog(
    bookId: String,
    currentPartIndex: Int,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("LibrisAudioPrefs", Context.MODE_PRIVATE) }
    var userApiKey by remember { mutableStateOf(prefs.getString("OPENROUTER_API_KEY", "") ?: "") }
    var isConfigOpen by remember { mutableStateOf(false) }
    var enforceOnlyFreeModels by remember { mutableStateOf(true) }

    var inputText by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    val messages = remember {
        mutableStateListOf(
            ChatBubble("1", "ai", "¡Hola! Soy tu asistente de lectura de Libris Audio. ¿Qué duda tienes sobre esta parte del libro?")
        )
    }
    val coroutineScope = rememberCoroutineScope()

    val quickQuestions = listOf(
        "¿Quién es el personaje principal?",
        "Hazme un resumen de esta parte",
        "Explícame la idea central"
    )

    fun sendMessage(msg: String) {
        if (msg.trim().isEmpty() || isLoading) return
        val userMsg = msg.trim()
        messages.add(ChatBubble(System.currentTimeMillis().toString(), "user", userMsg))
        inputText = ""
        isLoading = true

        coroutineScope.launch {
            try {
                val client = OkHttpClient()
                val json = JSONObject()
                json.put("book_id", bookId)
                json.put("part_index", currentPartIndex)
                json.put("user_message", userMsg)
                json.put("enforce_free_only", enforceOnlyFreeModels)
                if (userApiKey.isNotBlank()) {
                    json.put("user_openrouter_key", userApiKey.trim())
                }

                val body = json.toString().toRequestBody("application/json".toMediaType())
                val request = Request.Builder()
                    .url("https://libris-backend-z5fr.onrender.com/api/chat-book")
                    .post(body)
                    .build()

                val response = client.newCall(request).execute()
                val respStr = response.body?.string() ?: ""
                val replyJson = JSONObject(respStr)
                val replyText = replyJson.optString("reply", "No se pudo obtener respuesta de la IA.")

                messages.add(ChatBubble(System.currentTimeMillis().toString(), "ai", replyText))
            } catch (e: Exception) {
                messages.add(ChatBubble(System.currentTimeMillis().toString(), "ai", "Error de conexión con la IA. Inténtalo de nuevo."))
            } finally {
                isLoading = false
            }
        }
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = DarkSlate,
        scrimColor = Color(0x99000000)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = CyanAccent)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Pregúntale a la IA",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { isConfigOpen = !isConfigOpen }) {
                        Icon(
                            Icons.Default.Key,
                            contentDescription = "Configurar API Key",
                            tint = if (userApiKey.isNotBlank()) CyanAccent else TextMuted
                        )
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Cerrar", tint = TextMuted)
                    }
                }
            }

            // User API Key & Cost Safety Panel
            if (isConfigOpen) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = CardSurface),
                    shape = RoundedCornerShape(14.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = "?? Tu API Key de OpenRouter",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = CyanAccent
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Pega tu clave para usar tu cuota personal en cascada.",
                            fontSize = 11.sp,
                            color = TextMuted
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = userApiKey,
                            onValueChange = {
                                userApiKey = it
                                prefs.edit().putString("OPENROUTER_API_KEY", it).apply()
                            },
                            placeholder = { Text("sk-or-v1-...", fontSize = 12.sp, color = TextMuted) },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(10.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = CyanAccent,
                                unfocusedBorderColor = Color(0xFF334155),
                                focusedContainerColor = Color(0xFF0F172A),
                                unfocusedContainerColor = Color(0xFF0F172A),
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White
                            )
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        // Anti-Saldo Consumption Safety Switch
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Security, contentDescription = null, tint = CyanAccent, modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Column {
                                    Text("Escudo 100% Gratuito", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color.White)
                                    Text("Fuerza solo modelos :free sin tocar tu saldo", fontSize = 10.sp, color = TextMuted)
                                }
                            }
                            Switch(
                                checked = enforceOnlyFreeModels,
                                onCheckedChange = { enforceOnlyFreeModels = it },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = Color.Black,
                                    checkedTrackColor = CyanAccent
                                )
                            )
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Highlighted Pro Tip Box
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color(0xFF06373A), RoundedCornerShape(10.dp))
                                .padding(10.dp)
                        ) {
                            Row(verticalAlignment = Alignment.Top) {
                                Icon(
                                    Icons.Default.Lightbulb,
                                    contentDescription = null,
                                    tint = CyanAccent,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "?? TRUCO DE CUOTA: Si realizas una compra única de $10 de crédito en OpenRouter, tu límite de peticiones gratuitas aumenta permanentemente de 50 a 1,000 peticiones/día de por vida. El Escudo 100% Gratuito garantiza que tu saldo de $10 NUNCA sea consumido.",
                                    fontSize = 10.5.sp,
                                    color = Color(0xFFE0F2FE),
                                    lineHeight = 14.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Messages Container
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(220.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages) { item ->
                    val isUser = item.sender == "user"
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
                    ) {
                        Box(
                            modifier = Modifier
                                .widthIn(max = 280.dp)
                                .background(
                                    color = if (isUser) PurpleAccent else CardSurface,
                                    shape = RoundedCornerShape(14.dp)
                                )
                                .padding(12.dp)
                        ) {
                            Text(
                                text = item.text,
                                fontSize = 13.sp,
                                color = Color.White
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Quick Questions Chips
            Row(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                quickQuestions.forEach { q ->
                    Box(
                        modifier = Modifier
                            .background(CardSurface, RoundedCornerShape(10.dp))
                            .clickable { sendMessage(q) }
                            .padding(horizontal = 8.dp, vertical = 6.dp)
                    ) {
                        Text(q, fontSize = 10.sp, color = CyanAccent, fontWeight = FontWeight.Bold)
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Input Bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    placeholder = { Text("Haz una pregunta sobre el libro...", fontSize = 12.sp, color = TextMuted) },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = Color(0xFF334155),
                        focusedContainerColor = Color(0xFF0F172A),
                        unfocusedContainerColor = Color(0xFF0F172A),
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    )
                )

                Spacer(modifier = Modifier.width(8.dp))

                IconButton(
                    onClick = { sendMessage(inputText) },
                    modifier = Modifier
                        .size(48.dp)
                        .background(CyanAccent, RoundedCornerShape(24.dp))
                ) {
                    Icon(Icons.Default.Send, contentDescription = "Enviar", tint = Color.Black)
                }
            }
        }
    }
}
