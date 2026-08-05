package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.BookmarkAdd
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted

data class BookmarkItem(
    val id: String,
    val bookId: String,
    val partIndex: Int,
    val positionMs: Long,
    val note: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BookmarkDialog(
    bookTitle: String,
    currentPartIndex: Int,
    currentPositionMs: Long,
    bookmarks: List<BookmarkItem>,
    onAddBookmark: (String) -> Unit,
    onJumpToBookmark: (BookmarkItem) -> Unit,
    onDismiss: () -> Unit
) {
    var noteText by remember { mutableStateOf("") }

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
                    Icon(Icons.Default.Bookmark, contentDescription = null, tint = PurpleAccent)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Marcapáginas y Citas",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
                IconButton(onClick = onDismiss) {
                    Icon(Icons.Default.Close, contentDescription = "Cerrar", tint = TextMuted)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Card(
                colors = CardDefaults.cardColors(containerColor = CardSurface),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    val m = (currentPositionMs / 1000) / 60
                    val s = (currentPositionMs / 1000) % 60
                    Text(
                        text = "Guardar marca actual: Parte ${currentPartIndex + 1} (${String.format("%02d:%02d", m, s)})",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = CyanAccent
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    OutlinedTextField(
                        value = noteText,
                        onValueChange = { noteText = it },
                        placeholder = { Text("Nota opcional (ej: Cita importante...)", color = TextMuted, fontSize = 12.sp) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = PurpleAccent,
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedContainerColor = Color(0xFF0F172A),
                            unfocusedContainerColor = Color(0xFF0F172A),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = {
                            onAddBookmark(noteText.ifEmpty { "Marca de lectura" })
                            noteText = ""
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = PurpleAccent),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.align(Alignment.End)
                    ) {
                        Icon(Icons.Default.BookmarkAdd, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Guardar Marcapáginas", fontSize = 12.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text("Tus marcas en este libro:", fontSize = 12.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(8.dp))

            if (bookmarks.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(100.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text("Aún no has guardado marcapáginas.", fontSize = 12.sp, color = TextMuted)
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(bookmarks) { item ->
                        val m = (item.positionMs / 1000) / 60
                        val s = (item.positionMs / 1000) % 60
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = CardSurface,
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onJumpToBookmark(item) }
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = item.note,
                                        fontSize = 13.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White
                                    )
                                    Text(
                                        text = "Parte ${item.partIndex + 1} • ${String.format("%02d:%02d", m, s)}",
                                        fontSize = 11.sp,
                                        color = CyanAccent
                                    )
                                }
                                Text("Ir ▶", fontSize = 12.sp, color = PurpleAccent, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}
