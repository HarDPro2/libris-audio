package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import coil.compose.AsyncImage
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.data.model.BookCategories

@Composable
fun BookCard(
    book: Book,
    currentTheme: AppThemePreset,
    currentUserId: String = "",
    onBookClick: () -> Unit,
    onDeleteBook: ((Book) -> Unit)? = null,
    onEditBook: ((Book, String, String) -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val isOwner = currentUserId.isNotBlank() && book.addedBy == currentUserId
    var showMenu by remember { mutableStateOf(false) }
    var showEditDialog by remember { mutableStateOf(false) }
    var showDeleteConfirm by remember { mutableStateOf(false) }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0x441E293B))
            .clickable { onBookClick() }
    ) {
        Column {
            // Cover image
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(160.dp)
            ) {
                AsyncImage(
                    model = book.coverUrl ?: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300&h=400&fit=crop",
                    contentDescription = book.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
                // Gradient overlay at bottom
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(60.dp)
                        .align(Alignment.BottomCenter)
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(Color.Transparent, Color(0xDD0F172A))
                            )
                        )
                )
                // Category badge
                Surface(
                    modifier = Modifier
                        .align(Alignment.TopStart)
                        .padding(6.dp),
                    color = currentTheme.primary.copy(alpha = 0.9f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = book.category,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 3.dp)
                    )
                }
                // Owner menu button
                if (isOwner) {
                    Box(modifier = Modifier.align(Alignment.TopEnd)) {
                        IconButton(
                            onClick = { showMenu = true },
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                Icons.Default.MoreVert,
                                contentDescription = "Opciones",
                                tint = Color.White,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                        DropdownMenu(
                            expanded = showMenu,
                            onDismissRequest = { showMenu = false },
                            modifier = Modifier.background(Color(0xFF1E293B))
                        ) {
                            DropdownMenuItem(
                                text = { Text("Editar nombre/categoría", color = Color.White) },
                                onClick = { showMenu = false; showEditDialog = true },
                                leadingIcon = { Icon(Icons.Default.Edit, contentDescription = null, tint = currentTheme.primary) }
                            )
                            DropdownMenuItem(
                                text = { Text("Eliminar libro", color = Color(0xFFEF4444)) },
                                onClick = { showMenu = false; showDeleteConfirm = true },
                                leadingIcon = { Icon(Icons.Default.Delete, contentDescription = null, tint = Color(0xFFEF4444)) }
                            )
                        }
                    }
                }
                // Progress bar at bottom
                if (book.progressPercent > 0) {
                    LinearProgressIndicator(
                        progress = { book.progressPercent / 100f },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(3.dp)
                            .align(Alignment.BottomCenter),
                        color = currentTheme.secondary,
                        trackColor = Color(0x33FFFFFF)
                    )
                }
            }

            // Title and info
            Column(modifier = Modifier.padding(8.dp)) {
                Text(
                    text = book.title,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "${book.partsCount} parte${if (book.partsCount != 1) "s" else ""}",
                    fontSize = 11.sp,
                    color = Color(0xFF94A3B8)
                )
                if (book.progressPercent > 0) {
                    Text(
                        text = "${book.progressPercent}% completado",
                        fontSize = 10.sp,
                        color = currentTheme.secondary
                    )
                }
            }
        }
    }

    // Edit dialog
    if (showEditDialog) {
        EditBookDialog(
            book = book,
            currentTheme = currentTheme,
            onDismiss = { showEditDialog = false },
            onConfirm = { newTitle, newCategory ->
                showEditDialog = false
                onEditBook?.invoke(book, newTitle, newCategory)
            }
        )
    }

    // Delete confirmation
    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("Eliminar libro", color = Color.White) },
            text = { Text("¿Seguro que quieres eliminar \"${book.title}\"? Esta acción no se puede deshacer.", color = Color(0xFF94A3B8)) },
            confirmButton = {
                TextButton(onClick = { showDeleteConfirm = false; onDeleteBook?.invoke(book) }) {
                    Text("Eliminar", color = Color(0xFFEF4444))
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text("Cancelar", color = Color(0xFF94A3B8))
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }
}

@Composable
private fun EditBookDialog(
    book: Book,
    currentTheme: AppThemePreset,
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit
) {
    var title by remember { mutableStateOf(book.title) }
    var selectedCategory by remember { mutableStateOf(book.category) }
    var showCategoryDropdown by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = Color(0xFF1E293B)
        ) {
            Column(modifier = Modifier.padding(24.dp)) {
                Text("Editar libro", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 18.sp)
                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Título", color = Color(0xFF94A3B8)) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = currentTheme.primary,
                        unfocusedBorderColor = Color(0x44FFFFFF),
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    )
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Category picker
                Box {
                    OutlinedTextField(
                        value = selectedCategory,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Categoría", color = Color(0xFF94A3B8)) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { showCategoryDropdown = true },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = currentTheme.primary,
                            unfocusedBorderColor = Color(0x44FFFFFF),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )
                    DropdownMenu(
                        expanded = showCategoryDropdown,
                        onDismissRequest = { showCategoryDropdown = false },
                        modifier = Modifier.background(Color(0xFF1E293B))
                    ) {
                        BookCategories.ALL.forEach { cat ->
                            DropdownMenuItem(
                                text = { Text(cat, color = Color.White) },
                                onClick = { selectedCategory = cat; showCategoryDropdown = false }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    TextButton(onClick = onDismiss) { Text("Cancelar", color = Color(0xFF94A3B8)) }
                    Spacer(modifier = Modifier.width(8.dp))
                    Button(
                        onClick = { onConfirm(title.trim(), selectedCategory) },
                        enabled = title.isNotBlank(),
                        colors = ButtonDefaults.buttonColors(containerColor = currentTheme.primary)
                    ) { Text("Guardar") }
                }
            }
        }
    }
}
