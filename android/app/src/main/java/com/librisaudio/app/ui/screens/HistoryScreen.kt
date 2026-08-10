package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.librisaudio.app.R
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
    // Only books where the user has made progress (> 0%)
    val listenedBooks = books.filter { it.progressPercent > 0 }

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
        ) {
            // Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.History,
                    contentDescription = null,
                    tint = currentTheme.primary,
                    modifier = Modifier.size(26.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.hist_title),
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
            Text(
                text = stringResource(R.string.hist_subtitle),
                fontSize = 12.sp,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(20.dp))

            if (listenedBooks.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("🕐", fontSize = 48.sp)
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = stringResource(R.string.hist_empty_title),
                            color = TextMuted,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = stringResource(R.string.hist_empty_sub),
                            color = TextMuted.copy(alpha = 0.7f),
                            fontSize = 13.sp
                        )
                    }
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    contentPadding = PaddingValues(bottom = 120.dp)
                ) {
                    items(listenedBooks, key = { it.id }) { book ->
                        HistoryBookRow(
                            book = book,
                            currentTheme = currentTheme,
                            onClick = { onBookSelect(book) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HistoryBookRow(
    book: Book,
    currentTheme: AppThemePreset,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0x441E293B))
            .clickable { onClick() }
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Cover thumbnail
        Box(
            modifier = Modifier
                .size(width = 52.dp, height = 68.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(Color(0xFF1E293B))
        ) {
            AsyncImage(
                model = book.coverUrl ?: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=120&h=160&fit=crop",
                contentDescription = book.title,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
        }

        Spacer(modifier = Modifier.width(12.dp))

        // Info
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = book.title,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                fontSize = 15.sp,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                text = book.category,
                color = TextMuted,
                fontSize = 12.sp
            )
            Spacer(modifier = Modifier.height(6.dp))
            // Progress bar
            LinearProgressIndicator(
                progress = { book.progressPercent / 100f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .clip(RoundedCornerShape(2.dp)),
                color = currentTheme.secondary,
                trackColor = Color(0x33FFFFFF)
            )
            Spacer(modifier = Modifier.height(3.dp))
            Text(
                text = stringResource(R.string.hist_progress, book.progressPercent, book.currentPartIndex + 1, book.partsCount),
                color = currentTheme.secondary,
                fontSize = 11.sp
            )
        }

        Spacer(modifier = Modifier.width(8.dp))

        // Resume button
        Button(
            onClick = onClick,
            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
            colors = ButtonDefaults.buttonColors(containerColor = currentTheme.primary),
            modifier = Modifier.height(34.dp)
        ) {
            Text(stringResource(R.string.hist_resume), fontSize = 12.sp)
        }
    }
}
