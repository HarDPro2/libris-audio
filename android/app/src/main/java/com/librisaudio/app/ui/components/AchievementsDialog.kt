package com.librisaudio.app.ui.components

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class Achievement(
    val emoji: String,
    val title: String,
    val desc: String,
    val unlocked: Boolean
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AchievementsDialog(
    primary: Color,
    onDismiss: () -> Unit
) {
    val ctx = LocalContext.current
    val achievements = remember {
        val prefs = ctx.getSharedPreferences("libris_progress", Context.MODE_PRIVATE)
        val streak = prefs.getInt("stats_streak", 0)
        val totalHours = prefs.getInt("stats_total_min", 0) / 60.0
        val started = prefs.getStringSet("started_books", emptySet())?.size ?: 0

        listOf(
            Achievement("📖", "Primer paso", "Empieza tu primer libro", started >= 1),
            Achievement("📚", "Explorador", "Empieza 5 libros", started >= 5),
            Achievement("🏛️", "Bibliófilo", "Empieza 15 libros", started >= 15),
            Achievement("🔥", "En racha", "3 días seguidos", streak >= 3),
            Achievement("⚡", "Imparable", "7 días seguidos", streak >= 7),
            Achievement("👑", "Leyenda", "30 días seguidos", streak >= 30),
            Achievement("⏱️", "Maratonista", "10 horas escuchadas", totalHours >= 10),
            Achievement("🚀", "Devorador", "50 horas escuchadas", totalHours >= 50),
            Achievement("⭐", "Maestro", "100 horas escuchadas", totalHours >= 100)
        )
    }
    val unlockedCount = achievements.count { it.unlocked }

    ModalBottomSheet(onDismissRequest = onDismiss, containerColor = Color(0xFF0F172A)) {
        Column(modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.EmojiEvents, contentDescription = null, tint = Color(0xFFFACC15))
                Spacer(Modifier.width(8.dp))
                Text("Logros", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color.White)
                Spacer(Modifier.weight(1f))
                Text("$unlockedCount / ${achievements.size}", fontSize = 13.sp, color = primary, fontWeight = FontWeight.Bold)
            }
            Text("Sigue escuchando para desbloquearlos todos", fontSize = 11.sp,
                color = Color(0xFF94A3B8), modifier = Modifier.padding(top = 4.dp, bottom = 12.dp))

            LazyVerticalGrid(
                columns = GridCells.Fixed(3),
                modifier = Modifier.fillMaxWidth().heightIn(max = 420.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(achievements) { a ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .clip(RoundedCornerShape(14.dp))
                            .background(if (a.unlocked) primary.copy(alpha = 0.15f) else Color(0x11FFFFFF))
                            .padding(vertical = 12.dp, horizontal = 6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(52.dp)
                                .clip(CircleShape)
                                .background(if (a.unlocked) primary.copy(alpha = 0.25f) else Color(0x22FFFFFF)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(a.emoji, fontSize = 26.sp,
                                modifier = if (a.unlocked) Modifier else Modifier.alpha(0.35f))
                        }
                        Spacer(Modifier.height(6.dp))
                        Text(a.title, fontSize = 11.sp, fontWeight = FontWeight.Bold,
                            color = if (a.unlocked) Color.White else Color(0xFF64748B),
                            textAlign = TextAlign.Center, maxLines = 1)
                        Text(a.desc, fontSize = 9.sp, color = Color(0xFF94A3B8),
                            textAlign = TextAlign.Center, lineHeight = 11.sp, maxLines = 2)
                        if (!a.unlocked) {
                            Text("🔒", fontSize = 10.sp, modifier = Modifier.padding(top = 2.dp))
                        }
                    }
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}
