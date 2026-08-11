package com.librisaudio.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.librisaudio.app.R
import com.librisaudio.app.data.OfflineBook
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted

@Composable
fun DownloadsScreen(
    currentTheme: AppThemePreset,
    books: List<OfflineBook>,
    totalBytes: Long,
    onPlay: (String) -> Unit,
    onDelete: (String) -> Unit,
    onDeleteAll: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp)
        ) {
            Spacer(Modifier.height(16.dp))

            // Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Download, contentDescription = null, tint = currentTheme.primary, modifier = Modifier.size(26.dp))
                Spacer(Modifier.width(8.dp))
                Column {
                    Text(stringResource(R.string.nav_downloads), fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text(stringResource(R.string.downloads_subtitle), fontSize = 12.sp, color = TextMuted)
                }
            }

            Spacer(Modifier.height(16.dp))

            if (books.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("📥", fontSize = 44.sp)
                        Spacer(Modifier.height(12.dp))
                        Text(
                            stringResource(R.string.downloads_empty),
                            color = TextMuted,
                            fontSize = 13.sp,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            } else {
                // Summary + delete all
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        stringResource(R.string.downloads_summary, books.size, formatBytes(totalBytes)),
                        color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Medium
                    )
                    TextButton(onClick = onDeleteAll) {
                        Text(stringResource(R.string.downloads_delete_all), color = Color(0xFFEF4444), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
                Spacer(Modifier.height(8.dp))

                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    contentPadding = PaddingValues(bottom = 120.dp)
                ) {
                    items(books, key = { it.bookId }) { b ->
                        Surface(
                            shape = RoundedCornerShape(14.dp),
                            color = Color(0x441E293B),
                            modifier = Modifier.fillMaxWidth().clickable { onPlay(b.bookId) }
                        ) {
                            Row(
                                modifier = Modifier.padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                AsyncImage(
                                    model = b.coverUrl,
                                    contentDescription = null,
                                    contentScale = ContentScale.Crop,
                                    modifier = Modifier.size(56.dp).clip(RoundedCornerShape(10.dp))
                                )
                                Spacer(Modifier.width(12.dp))
                                Column(Modifier.weight(1f)) {
                                    Text(b.title, color = Color.White, fontSize = 14.sp,
                                        fontWeight = FontWeight.Bold, maxLines = 2)
                                    Text(
                                        stringResource(R.string.downloads_parts, b.partsCount, formatBytes(b.sizeBytes)) +
                                            if (!b.complete) " · ⏳" else "",
                                        color = TextMuted, fontSize = 11.sp
                                    )
                                }
                                Box(
                                    modifier = Modifier.size(40.dp).clip(RoundedCornerShape(20.dp))
                                        .background(currentTheme.primary)
                                        .clickable { onPlay(b.bookId) },
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(Icons.Default.PlayArrow, contentDescription = stringResource(R.string.player_play), tint = Color.White)
                                }
                                IconButton(onClick = { onDelete(b.bookId) }) {
                                    Icon(Icons.Default.Delete, contentDescription = stringResource(R.string.downloads_delete), tint = Color(0xFFEF4444))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun formatBytes(bytes: Long): String {
    if (bytes <= 0) return "0 MB"
    val mb = bytes / (1024.0 * 1024.0)
    return if (mb >= 1) String.format("%.1f MB", mb) else String.format("%.0f KB", bytes / 1024.0)
}
