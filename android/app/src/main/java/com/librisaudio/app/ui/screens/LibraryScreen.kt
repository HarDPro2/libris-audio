package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.data.model.BookCategories
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.components.BookCard
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted

private enum class LibraryTab { EXPLORAR, MI_BIBLIOTECA }

@Composable
fun LibraryScreen(
    books: List<Book>,                     // catálogo global (Explorar)
    personalBooks: List<Book>,             // libros del usuario (Mi Biblioteca)
    currentTheme: AppThemePreset,
    currentUserId: String,
    onBookSelect: (Book) -> Unit,
    onDeleteBook: (Book) -> Unit,
    onEditBook: (Book, String, String) -> Unit,
    lastBookId: String = "",
    onContinue: (Book) -> Unit = {},
    favorites: Set<String> = emptySet(),
    onToggleFavorite: (Book) -> Unit = {},
    modifier: Modifier = Modifier
) {
    var activeTab by remember { mutableStateOf(LibraryTab.EXPLORAR) }
    var activeCategory by remember { mutableStateOf("Todas") }
    var searchQuery by remember { mutableStateOf("") }

    // Source books depend on active tab
    val sourceBooks = if (activeTab == LibraryTab.EXPLORAR) books else personalBooks

    // Categories dynamically from the actual books (any category, sorted)
    val usedCategories = remember(sourceBooks) {
        val used = sourceBooks
            .mapNotNull { it.category.takeIf { c -> c.isNotBlank() } }
            .distinct()
            .sorted()
        listOf("Todas", "❤️ Favoritos") + used
    }

    // Filter by category then by search
    val filteredBooks = remember(sourceBooks, activeCategory, searchQuery, favorites) {
        var result = when (activeCategory) {
            "Todas"        -> sourceBooks
            "❤️ Favoritos" -> sourceBooks.filter { it.bookId in favorites }
            else           -> sourceBooks.filter { it.category == activeCategory }
        }

        if (searchQuery.isNotBlank()) {
            val q = searchQuery.lowercase()
            result = result.filter {
                it.title.lowercase().contains(q) ||
                it.author.lowercase().contains(q) ||
                it.category.lowercase().contains(q)
            }
        }
        result
    }

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Header
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Row {
                        Text("Libris", fontSize = 26.sp, fontWeight = FontWeight.Black, color = currentTheme.primary)
                        Text("Audio", fontSize = 26.sp, fontWeight = FontWeight.Black, color = currentTheme.secondary)
                    }
                    Text("Tu biblioteca de audiolibros", fontSize = 12.sp, color = TextMuted)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Tabs — Explorar / Mi Biblioteca
            Row(
                modifier = Modifier
                    .clip(RoundedCornerShape(12.dp))
                    .background(Color(0x331E293B))
                    .padding(4.dp)
            ) {
                TabButton(
                    text = "Explorar",
                    selected = activeTab == LibraryTab.EXPLORAR,
                    accentColor = currentTheme.primary,
                    onClick = { activeTab = LibraryTab.EXPLORAR; activeCategory = "Todas" },
                    modifier = Modifier.weight(1f)
                )
                TabButton(
                    text = "Mi Biblioteca",
                    selected = activeTab == LibraryTab.MI_BIBLIOTECA,
                    accentColor = currentTheme.primary,
                    onClick = { activeTab = LibraryTab.MI_BIBLIOTECA; activeCategory = "Todas" },
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Search
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = { Text("Buscar por título, autor o categoría…", color = TextMuted, fontSize = 13.sp) },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = TextMuted) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = currentTheme.primary,
                    unfocusedBorderColor = Color(0x44FFFFFF),
                    focusedContainerColor = Color(0xAA1E293B),
                    unfocusedContainerColor = Color(0x881E293B),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Continuar escuchando — tarjeta destacada del último libro con progreso
            val continueBook = remember(books, lastBookId) {
                books.firstOrNull { it.bookId == lastBookId && it.progressPercent > 0 }
            }
            if (activeTab == LibraryTab.EXPLORAR && continueBook != null && searchQuery.isBlank()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(16.dp))
                        .background(
                            Brush.horizontalGradient(
                                listOf(currentTheme.primary.copy(alpha = 0.30f), Color(0x551E293B))
                            )
                        )
                        .clickable { onContinue(continueBook) }
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    AsyncImage(
                        model = continueBook.coverUrl,
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.size(52.dp).clip(RoundedCornerShape(10.dp))
                    )
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text("CONTINUAR ESCUCHANDO", fontSize = 9.sp, fontWeight = FontWeight.Bold,
                            color = currentTheme.secondary, letterSpacing = 1.sp)
                        Text(continueBook.title, fontSize = 14.sp, fontWeight = FontWeight.Bold,
                            color = Color.White, maxLines = 1)
                        Text("Parte ${continueBook.currentPartIndex + 1} · ${continueBook.progressPercent}%",
                            fontSize = 11.sp, color = TextMuted)
                    }
                    Box(
                        modifier = Modifier.size(42.dp).clip(CircleShape).background(currentTheme.primary),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Default.PlayArrow, contentDescription = "Continuar", tint = Color.White)
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Category pills (horizontal scroll)
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(end = 8.dp)
            ) {
                items(usedCategories) { cat ->
                    val isActive = cat == activeCategory
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(20.dp))
                            .background(if (isActive) currentTheme.primary else Color(0x441E293B))
                            .clickable { activeCategory = cat }
                            .padding(horizontal = 14.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = cat,
                            fontSize = 12.sp,
                            fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
                            color = if (isActive) Color.White else TextMuted
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Content
            when {
                filteredBooks.isEmpty() && sourceBooks.isEmpty() && activeTab == LibraryTab.MI_BIBLIOTECA -> {
                    EmptyState(
                        emoji = "📚",
                        title = "Tu biblioteca está vacía",
                        subtitle = "Ve a Explorar para empezar a escuchar libros",
                        textMuted = TextMuted
                    )
                }
                filteredBooks.isEmpty() && searchQuery.isNotBlank() -> {
                    EmptyState(
                        emoji = "🔍",
                        title = "Sin resultados",
                        subtitle = "No encontramos libros que coincidan con \"$searchQuery\"",
                        textMuted = TextMuted
                    )
                }
                filteredBooks.isEmpty() -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = currentTheme.primary)
                    }
                }
                else -> {
                    LazyVerticalGrid(
                        columns = GridCells.Fixed(2),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                        contentPadding = PaddingValues(bottom = 120.dp),
                        modifier = Modifier.fillMaxSize()
                    ) {
                        items(filteredBooks, key = { it.id }) { book ->
                            BookCard(
                                book = book,
                                currentTheme = currentTheme,
                                currentUserId = currentUserId,
                                onBookClick = { onBookSelect(book) },
                                onDeleteBook = onDeleteBook,
                                onEditBook = onEditBook,
                                isFavorite = book.bookId in favorites,
                                onToggleFavorite = onToggleFavorite
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TabButton(
    text: String,
    selected: Boolean,
    accentColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(9.dp))
            .background(if (selected) accentColor else Color.Transparent)
            .clickable { onClick() }
            .padding(vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            fontSize = 13.sp,
            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
            color = if (selected) Color.White else TextMuted
        )
    }
}

@Composable
private fun EmptyState(emoji: String, title: String, subtitle: String, textMuted: Color) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(emoji, fontSize = 40.sp)
            Spacer(modifier = Modifier.height(12.dp))
            Text(title, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 16.sp)
            Spacer(modifier = Modifier.height(6.dp))
            Text(subtitle, color = textMuted, fontSize = 13.sp)
        }
    }
}
