package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.model.Book
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.components.BookCard
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted

@Composable
fun LibraryScreen(
    books: List<Book>,
    currentTheme: AppThemePreset,
    onSelectTheme: (AppThemePreset) -> Unit,
    onBookSelect: (Book) -> Unit,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }

    val filteredBooks = remember(searchQuery, books) {
        if (searchQuery.isEmpty()) books
        else books.filter {
            it.title.contains(searchQuery, ignoreCase = true) ||
            it.category.contains(searchQuery, ignoreCase = true)
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        // Animated Canvas Mesh Gradient Background
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Header Title
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "Libris",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Black,
                    color = currentTheme.primary
                )
                Text(
                    text = "Audio",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Black,
                    color = currentTheme.secondary
                )
            }

            Text(
                text = "Convierte tus libros en audio neuronal",
                fontSize = 12.sp,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Theme Switcher Selector Chips
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
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = preset.title,
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            color = if (isSelected) Color.White else TextMuted
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Search Box
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = { Text("Buscar por título o categoría...", color = TextMuted) },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = TextMuted) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = currentTheme.primary,
                    unfocusedBorderColor = Color(0x44FFFFFF),
                    focusedContainerColor = Color(0xAA1E293B),
                    unfocusedContainerColor = Color(0x881E293B),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Books Grid
            if (filteredBooks.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (books.isEmpty()) "Cargando biblioteca..." else "No se encontraron libros",
                        color = TextMuted,
                        fontSize = 14.sp
                    )
                }
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Fixed(2),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    contentPadding = PaddingValues(bottom = 100.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    items(filteredBooks, key = { it.id }) { book ->
                        BookCard(
                            book = book,
                            onBookClick = { onBookSelect(book) }
                        )
                    }
                }
            }
        }
    }
}

