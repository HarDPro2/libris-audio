package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.model.VoiceCatalog
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.TextMuted

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceSelectorDialog(
    selectedVoiceId: String,
    onSelectVoice: (String) -> Unit,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = DarkSlate,
        scrimColor = Color(0x99000000)
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.RecordVoiceOver, contentDescription = null, tint = CyanAccent)
                Spacer(Modifier.width(8.dp))
                Text("Voz del Narrador", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color.White)
            }
            Text(
                "Voces neurales de Microsoft Azure. Se aplica al instante — cámbiala cuando quieras.",
                fontSize = 11.sp, color = TextMuted, modifier = Modifier.padding(top = 4.dp, bottom = 10.dp)
            )

            LazyColumn(
                modifier = Modifier.fillMaxWidth().heightIn(max = 380.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(VoiceCatalog.voices) { voice ->
                    val isSelected = voice.id == selectedVoiceId
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (isSelected) CyanAccent.copy(alpha = 0.18f) else Color(0x22FFFFFF))
                            .clickable { onSelectVoice(voice.id); onDismiss() }
                            .padding(horizontal = 14.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(voice.flag, fontSize = 22.sp)
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                voice.name,
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (isSelected) Color.White else Color(0xFFE2E8F0)
                            )
                            Text("${voice.country} · ${voice.gender}", fontSize = 11.sp, color = TextMuted)
                        }
                        if (isSelected) {
                            Icon(Icons.Default.Check, contentDescription = "Seleccionada", tint = CyanAccent)
                        }
                    }
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}
