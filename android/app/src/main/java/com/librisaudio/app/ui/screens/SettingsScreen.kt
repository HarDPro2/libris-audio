package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted

@Composable
fun SettingsScreen(
    currentTheme: AppThemePreset,
    onSelectTheme: (AppThemePreset) -> Unit,
    modifier: Modifier = Modifier
) {
    var openRouterKey by remember { mutableStateOf("") }
    var enforceFreeOnly by remember { mutableStateOf(true) }

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = null,
                    tint = currentTheme.primary,
                    modifier = Modifier.size(28.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Ajustes del Sistema",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }

            Text(
                text = "Personalización visual e Inteligencia Artificial",
                fontSize = 12.sp,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Section 1: Themes
            Text("Tema Visual", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 16.sp)
            Spacer(modifier = Modifier.height(8.dp))

            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                items(AppThemePreset.values()) { preset ->
                    val isSelected = currentTheme == preset
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (isSelected) preset.primary else Color(0x331E293B))
                            .clickable { onSelectTheme(preset) }
                            .padding(horizontal = 16.dp, vertical = 10.dp)
                    ) {
                        Text(
                            text = preset.title,
                            fontSize = 13.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            color = if (isSelected) Color.White else TextMuted
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Section 2: AI Protection
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0x331E293B)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Security,
                            contentDescription = null,
                            tint = Color(0xFF10B981),
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Escudo 100% Gratuito (Zero Balance)",
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            fontSize = 14.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Forzar solo modelos gratuitas (:free)",
                            color = TextMuted,
                            fontSize = 12.sp,
                            modifier = Modifier.weight(1f)
                        )
                        Switch(
                            checked = enforceFreeOnly,
                            onCheckedChange = { enforceFreeOnly = it },
                            colors = SwitchDefaults.colors(checkedThumbColor = currentTheme.primary)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Section 3: OpenRouter BYOK
            Text("API Key de OpenRouter (Opcional)", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
            Spacer(modifier = Modifier.height(4.dp))
            Text("Trae tu propia clave para saltar cuotas compartidas", color = TextMuted, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(8.dp))

            OutlinedTextField(
                value = openRouterKey,
                onValueChange = { openRouterKey = it },
                placeholder = { Text("sk-or-v1-...", color = TextMuted) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = currentTheme.primary,
                    unfocusedBorderColor = Color(0x44FFFFFF),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text("Versión de Servidor", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 14.sp)
            Text("Google Cloud Run • Appwrite 24/7 • Cloudflare R2", color = TextMuted, fontSize = 12.sp)
        }
    }
}
