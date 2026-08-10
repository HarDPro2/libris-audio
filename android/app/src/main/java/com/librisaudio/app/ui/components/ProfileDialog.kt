package com.librisaudio.app.ui.components

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.librisaudio.app.R
import androidx.compose.ui.window.DialogProperties
import com.librisaudio.app.data.model.AvatarCatalog
import com.librisaudio.app.data.model.UserProfile
import com.librisaudio.app.ui.theme.TextMuted

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileDialog(
    initial: UserProfile,
    email: String,
    primary: Color,
    onSave: (UserProfile) -> Unit,
    onDismiss: () -> Unit
) {
    val ctx = LocalContext.current
    var name by remember { mutableStateOf(initial.displayName) }
    var avatarId by remember { mutableStateOf(initial.avatarId) }
    var photoUri by remember { mutableStateOf(initial.photoUri) }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            try {
                ctx.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            } catch (_: Exception) {}
            photoUri = uri.toString()
        }
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            modifier = Modifier.fillMaxWidth(0.94f).fillMaxHeight(0.92f),
            shape = RoundedCornerShape(22.dp),
            color = Color(0xFF0F172A)
        ) {
            Column(modifier = Modifier.fillMaxSize().padding(20.dp)) {
                Text(stringResource(R.string.profile_title), fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
                Spacer(Modifier.height(14.dp))

                // Vista previa
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ProfileAvatar(UserProfile(name, avatarId, photoUri), 72.dp)
                    Spacer(Modifier.width(14.dp))
                    Column {
                        Text(name.ifBlank { stringResource(R.string.profile_your_name) },
                            fontSize = 17.sp, fontWeight = FontWeight.Bold,
                            color = if (name.isBlank()) TextMuted else Color.White)
                        Text(email, fontSize = 12.sp, color = TextMuted)
                    }
                }

                Spacer(Modifier.height(16.dp))

                OutlinedTextField(
                    value = name,
                    onValueChange = { if (it.length <= 24) name = it },
                    label = { Text(stringResource(R.string.profile_display_name)) },
                    placeholder = { Text(stringResource(R.string.profile_name_hint)) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = primary,
                        unfocusedBorderColor = Color(0x33FFFFFF),
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedContainerColor = Color(0x11FFFFFF),
                        unfocusedContainerColor = Color(0x11FFFFFF)
                    )
                )

                Spacer(Modifier.height(12.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Button(
                        onClick = { picker.launch(arrayOf("image/*")) },
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = primary)
                    ) {
                        Text(stringResource(R.string.profile_upload_photo), fontSize = 13.sp)
                    }
                    if (photoUri.isNotBlank()) {
                        Spacer(Modifier.width(8.dp))
                        TextButton(onClick = { photoUri = "" }) {
                            Text(stringResource(R.string.profile_remove_photo), color = Color(0xFFEF4444), fontSize = 13.sp)
                        }
                    }
                }

                Spacer(Modifier.height(12.dp))
                Text(stringResource(R.string.profile_choose_avatar), fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color.White)
                Spacer(Modifier.height(8.dp))

                LazyVerticalGrid(
                    columns = GridCells.Fixed(4),
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(AvatarCatalog.avatars) { av ->
                        val selected = photoUri.isBlank() && avatarId == av.id
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.clickable { avatarId = av.id; photoUri = "" }
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(56.dp)
                                    .clip(CircleShape)
                                    .background(Brush.linearGradient(listOf(av.c1, av.c2)))
                                    .then(if (selected) Modifier.border(3.dp, Color.White, CircleShape) else Modifier),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(av.emoji, fontSize = 24.sp)
                            }
                            Spacer(Modifier.height(3.dp))
                            Text(
                                av.name, fontSize = 8.5.sp, color = if (selected) Color.White else TextMuted,
                                maxLines = 1, textAlign = TextAlign.Center,
                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                            )
                        }
                    }
                }

                Spacer(Modifier.height(12.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedButton(onClick = onDismiss, modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp)) {
                        Text(stringResource(R.string.action_cancel), color = TextMuted)
                    }
                    Button(
                        onClick = { onSave(UserProfile(name.trim(), avatarId, photoUri)); onDismiss() },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = primary)
                    ) {
                        Text(stringResource(R.string.action_save), fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}
