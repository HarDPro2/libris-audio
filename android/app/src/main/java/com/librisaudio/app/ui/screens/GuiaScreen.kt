package com.librisaudio.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.R
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.CardSurface
import com.librisaudio.app.ui.theme.DarkSlate
import com.librisaudio.app.ui.theme.TextMuted

/**
 * "Todo lo que puedes hacer" — catalogo de funciones de la app.
 *
 * Regla de esta pantalla: solo entra lo que EXISTE y funciona hoy. Nada de
 * "proximamente". Una guia que promete de mas es peor que no tener guia,
 * porque el usuario busca el boton, no lo encuentra y deja de fiarse del resto.
 *
 * Cada funcion se describe con dos frases: que hace y donde se toca. El "donde"
 * es lo que realmente falta en las apps y lo que hace que la gente no descubra
 * la mitad de lo que ya pago.
 */

private data class Funcion(
    val emoji: String,
    val nombre: Int,      // R.string...
    val queHace: Int,
    val comoUsar: Int
)

private data class Grupo(
    val emoji: String,
    val titulo: Int,
    val funciones: List<Funcion>
)

private val GUIA: List<Grupo> = listOf(
    Grupo("📚", R.string.guia_g_library, listOf(
        Funcion("📤", R.string.guia_upload_t,     R.string.guia_upload_d,     R.string.guia_upload_h),
        Funcion("🔍", R.string.guia_ocr_t,        R.string.guia_ocr_d,        R.string.guia_ocr_h),
        Funcion("🌐", R.string.guia_lang_t,       R.string.guia_lang_d,       R.string.guia_lang_h),
        Funcion("✏️", R.string.guia_edit_t,       R.string.guia_edit_d,       R.string.guia_edit_h),
        Funcion("🗑️", R.string.guia_delete_t,     R.string.guia_delete_d,     R.string.guia_delete_h),
        Funcion("⭐", R.string.guia_fav_t,        R.string.guia_fav_d,        R.string.guia_fav_h)
    )),
    Grupo("🎧", R.string.guia_g_listen, listOf(
        Funcion("📖", R.string.guia_modes_t,      R.string.guia_modes_d,      R.string.guia_modes_h),
        Funcion("🗣️", R.string.guia_voices_t,     R.string.guia_voices_d,     R.string.guia_voices_h),
        Funcion("⚡", R.string.guia_speed_t,      R.string.guia_speed_d,      R.string.guia_speed_h),
        Funcion("✨", R.string.guia_karaoke_t,    R.string.guia_karaoke_d,    R.string.guia_karaoke_h),
        Funcion("🔖", R.string.guia_marks_t,      R.string.guia_marks_d,      R.string.guia_marks_h),
        Funcion("😴", R.string.guia_sleep_t,      R.string.guia_sleep_d,      R.string.guia_sleep_h),
        Funcion("🚗", R.string.guia_car_t,        R.string.guia_car_d,        R.string.guia_car_h),
        Funcion("🎙️", R.string.guia_voicecmd_t,   R.string.guia_voicecmd_d,   R.string.guia_voicecmd_h)
    )),
    Grupo("🎨", R.string.guia_g_immersive, listOf(
        Funcion("🖼️", R.string.guia_frames_t,     R.string.guia_frames_d,     R.string.guia_frames_h),
        Funcion("🎇", R.string.guia_fx_t,         R.string.guia_fx_d,         R.string.guia_fx_h),
        Funcion("🎵", R.string.guia_music_t,      R.string.guia_music_d,      R.string.guia_music_h),
        Funcion("🔠", R.string.guia_easy_t,       R.string.guia_easy_d,       R.string.guia_easy_h),
        Funcion("🌈", R.string.guia_theme_t,      R.string.guia_theme_d,      R.string.guia_theme_h)
    )),
    Grupo("🤖", R.string.guia_g_study, listOf(
        Funcion("💬", R.string.guia_chat_t,       R.string.guia_chat_d,       R.string.guia_chat_h),
        Funcion("📊", R.string.guia_stats_t,      R.string.guia_stats_d,      R.string.guia_stats_h)
    )),
    Grupo("📶", R.string.guia_g_anywhere, listOf(
        Funcion("⬇️", R.string.guia_offline_t,    R.string.guia_offline_d,    R.string.guia_offline_h),
        Funcion("🔄", R.string.guia_sync_t,       R.string.guia_sync_d,       R.string.guia_sync_h),
        Funcion("🌎", R.string.guia_applang_t,    R.string.guia_applang_d,    R.string.guia_applang_h),
        Funcion("⬆️", R.string.guia_update_t,     R.string.guia_update_d,     R.string.guia_update_h)
    ))
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GuiaScreen(
    currentTheme: AppThemePreset,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Solo un grupo abierto a la vez: con 24 funciones, todo desplegado es un
    // muro de texto que nadie lee.
    var abierto by remember { mutableStateOf(0) }

    Column(modifier = modifier.fillMaxSize().background(DarkSlate)) {
        TopAppBar(
            title = {
                Text(
                    stringResource(R.string.guia_title),
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, contentDescription = null, tint = Color.White)
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkSlate)
        )

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 120.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item {
                Text(
                    stringResource(R.string.guia_intro),
                    fontSize = 13.sp,
                    color = TextMuted,
                    modifier = Modifier.padding(bottom = 4.dp)
                )
            }

            items(GUIA.size) { i ->
                val grupo = GUIA[i]
                val expandido = abierto == i
                Surface(
                    shape = RoundedCornerShape(14.dp),
                    color = CardSurface,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { abierto = if (expandido) -1 else i }
                                .padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(grupo.emoji, fontSize = 20.sp)
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                stringResource(grupo.titulo),
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White,
                                modifier = Modifier.weight(1f)
                            )
                            Text(
                                "${grupo.funciones.size}",
                                fontSize = 12.sp,
                                color = currentTheme.secondary,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Icon(
                                if (expandido) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                contentDescription = null,
                                tint = TextMuted
                            )
                        }

                        AnimatedVisibility(visible = expandido) {
                            Column(
                                modifier = Modifier.padding(
                                    start = 14.dp, end = 14.dp, bottom = 14.dp
                                ),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                grupo.funciones.forEach { f -> FilaFuncion(f, currentTheme) }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilaFuncion(f: Funcion, currentTheme: AppThemePreset) {
    Row(modifier = Modifier.fillMaxWidth()) {
        Text(f.emoji, fontSize = 17.sp, modifier = Modifier.padding(end = 10.dp, top = 1.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                stringResource(f.nombre),
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                stringResource(f.queHace),
                fontSize = 12.sp,
                color = Color(0xFFCBD5E1),
                lineHeight = 16.sp
            )
            Spacer(modifier = Modifier.height(3.dp))
            Row {
                Text(
                    "▸ ",
                    fontSize = 11.sp,
                    color = currentTheme.secondary,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    stringResource(f.comoUsar),
                    fontSize = 11.sp,
                    color = currentTheme.secondary,
                    lineHeight = 15.sp
                )
            }
        }
    }
}
