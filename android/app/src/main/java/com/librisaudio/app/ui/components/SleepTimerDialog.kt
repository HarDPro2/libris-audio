package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bedtime
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted

enum class SleepTimerOption(val label: String, val minutes: Int) {
    OFF("Desactivado", 0),
    MIN_15("15 minutos", 15),
    MIN_30("30 minutos", 30),
    MIN_45("45 minutos", 45),
    MIN_60("60 minutos", 60),
    END_OF_PART("Al terminar la parte actual", -1)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SleepTimerDialog(
    selectedOption: SleepTimerOption,
    remainingSeconds: Long,
    onSelectOption: (SleepTimerOption) -> Unit,
    onDismiss: () -> Unit
) {
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Bedtime, contentDescription = null, tint = PurpleAccent)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Temporizador de Sueño",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
                IconButton(onClick = onDismiss) {
                    Icon(Icons.Default.Close, contentDescription = "Cerrar", tint = TextMuted)
                }
            }

            if (remainingSeconds > 0) {
                Spacer(modifier = Modifier.height(8.dp))
                val m = remainingSeconds / 60
                val s = remainingSeconds % 60
                Text(
                    text = "Tiempo restante: ${String.format("%02d:%02d", m, s)} (Fade-out suave activado)",
                    fontSize = 12.sp,
                    color = PurpleAccent,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(SleepTimerOption.values()) { option ->
                    val isSelected = selectedOption == option
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = if (isSelected) PurpleAccent else CardSurface,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectOption(option) }
                    ) {
                        Row(
                            modifier = Modifier.padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = option.label,
                                fontSize = 14.sp,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                color = Color.White
                            )
                        }
                    }
                }
            }
        }
    }
}
