package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.R
import com.librisaudio.app.data.model.BackgroundMusicCatalog
import com.librisaudio.app.data.model.GenreMusic
import com.librisaudio.app.data.model.MusicTrack
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.CyanAccent
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.PurpleAccent
import com.librisaudio.app.ui.theme.TextMuted

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MusicSelectorDialog(
    selectedTrack: MusicTrack?,
    backgroundVolume: Float,
    // META 3.7 — marco del libro abierto. Si viene, el selector pone arriba las
    // pistas que pegan con ese genero. Si es null se comporta como antes.
    estiloGenero: BookBindingStyle? = null,
    aleatorio: Boolean = false,
    onToggleAleatorio: (Boolean) -> Unit = {},
    onSelectTrack: (MusicTrack?) -> Unit,
    onVolumeChange: (Float) -> Unit,
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
                    Icon(Icons.Default.MusicNote, contentDescription = null, tint = PurpleAccent)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = stringResource(R.string.music_title),
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
                IconButton(onClick = onDismiss) {
                    Icon(Icons.Default.Close, contentDescription = stringResource(R.string.action_close), tint = TextMuted)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                colors = CardDefaults.cardColors(containerColor = CardSurface),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.VolumeUp, contentDescription = null, tint = CyanAccent)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(stringResource(R.string.music_volume), fontSize = 13.sp, color = Color.White)
                        }
                        Text("${(backgroundVolume * 100).toInt()}%", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = CyanAccent)
                    }

                    Slider(
                        value = backgroundVolume,
                        onValueChange = onVolumeChange,
                        valueRange = 0f..1f,
                        colors = SliderDefaults.colors(
                            thumbColor = CyanAccent,
                            activeTrackColor = CyanAccent,
                            inactiveTrackColor = Color(0xFF334155)
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(stringResource(R.string.music_choose), fontSize = 12.sp, color = TextMuted)
            Spacer(modifier = Modifier.height(8.dp))

            val recomendadas = remember(estiloGenero) {
                if (estiloGenero == null) emptyList()
                else GenreMusic.pistasPara(estiloGenero)
            }
            val resto = remember(recomendadas) {
                BackgroundMusicCatalog.tracks.filter { t -> recomendadas.none { it.id == t.id } }
            }

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(320.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Aleatorio arriba del todo: es el modo que mas se va a usar.
                item {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = if (aleatorio) PurpleAccent else CardSurface,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onToggleAleatorio(!aleatorio) }
                    ) {
                        Row(
                            modifier = Modifier.padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    stringResource(R.string.music_shuffle),
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                                Text(
                                    stringResource(R.string.music_shuffle_hint),
                                    fontSize = 11.sp,
                                    color = if (aleatorio) Color.White.copy(alpha = 0.8f) else TextMuted
                                )
                            }
                            if (aleatorio) Text("\u25B6", fontSize = 16.sp)
                        }
                    }
                }

                item {
                    val isSelected = selectedTrack == null && !aleatorio
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = if (isSelected) PurpleAccent else CardSurface,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectTrack(null) }
                    ) {
                        Row(
                            modifier = Modifier.padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(stringResource(R.string.music_none), fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }

                if (recomendadas.isEmpty()) {
                    items(BackgroundMusicCatalog.tracks) { track ->
                        PistaFila(track, selectedTrack?.id == track.id) { onSelectTrack(track) }
                    }
                } else {
                    item {
                        EncabezadoSeccion(
                            stringResource(R.string.music_for_genre, estiloGenero!!.title)
                        )
                    }
                    items(recomendadas) { track ->
                        PistaFila(track, selectedTrack?.id == track.id) { onSelectTrack(track) }
                    }
                    if (resto.isNotEmpty()) {
                        item { EncabezadoSeccion(stringResource(R.string.music_rest)) }
                        items(resto) { track ->
                            PistaFila(track, selectedTrack?.id == track.id) { onSelectTrack(track) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun EncabezadoSeccion(texto: String) {
    Text(
        text = texto,
        fontSize = 11.sp,
        fontWeight = FontWeight.Bold,
        color = CyanAccent,
        modifier = Modifier.padding(top = 6.dp, bottom = 2.dp)
    )
}

@Composable
private fun PistaFila(track: MusicTrack, isSelected: Boolean, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = if (isSelected) PurpleAccent else CardSurface,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = track.title,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "${track.composer} \u2022 ${track.category}",
                    fontSize = 11.sp,
                    color = if (isSelected) Color.White.copy(alpha = 0.8f) else TextMuted
                )
            }
            if (isSelected) {
                Text("\u25B6", fontSize = 16.sp)
            }
        }
    }
}
