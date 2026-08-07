package com.librisaudio.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.em
import coil.compose.AsyncImage
import com.librisaudio.app.data.model.AvatarCatalog
import com.librisaudio.app.data.model.UserProfile

/** Muestra la foto del usuario si existe, si no el avatar (degradado + emoji). */
@Composable
fun ProfileAvatar(profile: UserProfile, size: Dp, modifier: Modifier = Modifier) {
    if (profile.photoUri.isNotBlank()) {
        AsyncImage(
            model = profile.photoUri,
            contentDescription = "Foto de perfil",
            contentScale = ContentScale.Crop,
            modifier = modifier.size(size).clip(CircleShape)
        )
    } else {
        val avatar = AvatarCatalog.byId(profile.avatarId)
        Box(
            modifier = modifier
                .size(size)
                .clip(CircleShape)
                .background(Brush.linearGradient(listOf(avatar.c1, avatar.c2))),
            contentAlignment = Alignment.Center
        ) {
            Text(avatar.emoji, fontSize = (size.value * 0.5f).sp)
        }
    }
}
