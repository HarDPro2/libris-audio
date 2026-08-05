package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted

@Composable
fun HistoryScreen(
    books: List<Book>,
    currentTheme: AppThemePreset,
    onBookSelect: (Book) -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.History,
                    contentDescription = null,
                    tint = currentTheme.primary,
                    modifier = Modifier.size(28.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Historial de Lectura",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }

            Text(
                text = "Tus audiolibros recientes y progreso en la nube",
                fontSize = 12.sp,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(16.dp))

            if (books.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text("No hay lecturas recientes", color = TextMuted)
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    contentPadding = PaddingValues(bottom = 100.dp)
                ) {
                    items(books) { book ->
                        Card(
                            onClick = { onBookSelect(book) },
                            colors = CardDefaults.cardColors(containerColor = Color(0x331E293B)),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = book.title,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White,
                                        fontSize = 16.sp
                                    )
                                    Text(
                                        text = "${book.category} • ${book.partsCount} partes",
                                        color = TextMuted,
                                        fontSize = 12.sp
                                    )
                                }

                                Button(
                                    onClick = { onBookSelect(book) },
                                    colors = ButtonDefaults.buttonColors(containerColor = currentTheme.primary)
                                ) {
                                    Text("Reanudar")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
