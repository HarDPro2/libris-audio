package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FormatSize
import androidx.compose.material.icons.filled.NavigateBefore
import androidx.compose.material.icons.filled.NavigateNext
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.model.Book

enum class BookBindingStyle(
    val title: String,
    val coverBorderColor: Color,
    val paperColor: Color,
    val textColor: Color,
    val accentColor: Color
) {
    LUXURY_LEATHER(
        title = "?? Cuero de Lujo",
        coverBorderColor = Color(0xFF422006),
        paperColor = Color(0xFFFEF3C7),
        textColor = Color(0xFF1E1003),
        accentColor = Color(0xFFD97706)
    ),
    MINIMALIST(
        title = "?? Minimalista",
        coverBorderColor = Color(0xFF334155),
        paperColor = Color(0xFFF8FAFC),
        textColor = Color(0xFF0F172A),
        accentColor = Color(0xFF0284C7)
    ),
    VELVET_NIGHT(
        title = "?? Velvet Nocturno",
        coverBorderColor = Color(0xFF1E1B4B),
        paperColor = Color(0xFF0F172A),
        textColor = Color(0xFFF1F5F9),
        accentColor = Color(0xFF818CF8)
    ),
    ANCIENT_PARCHMENT(
        title = "?? Pergamino Antiguo",
        coverBorderColor = Color(0xFF78350F),
        paperColor = Color(0xFFFDE68A),
        textColor = Color(0xFF451A03),
        accentColor = Color(0xFFB45309)
    )
}

@Composable
fun VirtualBookFrame(
    book: Book,
    textPart: String,
    currentPartIndex: Int,
    isPlaying: Boolean,
    onNextPart: () -> Unit,
    onPreviousPart: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedStyle by remember { mutableStateOf(BookBindingStyle.LUXURY_LEATHER) }
    var fontSizeSp by remember { mutableStateOf(16) }
    var isSerifFont by remember { mutableStateOf(true) }

    // Page flip 3D animation degree
    var flipAngle by remember { mutableStateOf(0f) }
    val animatedAngle by animateFloatAsState(
        targetValue = flipAngle,
        animationSpec = spring(stiffness = Spring.StiffnessLow),
        label = "PageFlip"
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(12.dp)
    ) {
        // Toolbar: Style & Font Controls
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Style Selector Pills
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                BookBindingStyle.values().forEach { style ->
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (selectedStyle == style) style.accentColor else Color(0x331E293B))
                            .clickable { selectedStyle = style }
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = style.title,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (selectedStyle == style) Color.White else Color.Gray
                        )
                    }
                }
            }

            // Font Controls
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { if (fontSizeSp > 12) fontSizeSp -= 2 }) {
                    Text("A-", fontSize = 12.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { if (fontSizeSp < 24) fontSizeSp += 2 }) {
                    Text("A+", fontSize = 14.sp, color = Color.White, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { isSerifFont = !isSerifFont }) {
                    Text(if (isSerifFont) "Serif" else "Sans", fontSize = 11.sp, color = Color.White)
                }
            }
        }

        // 3D Book Frame Container
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .shadow(16.dp, RoundedCornerShape(16.dp))
                .border(6.dp, selectedStyle.coverBorderColor, RoundedCornerShape(16.dp))
                .clip(RoundedCornerShape(16.dp))
                .background(selectedStyle.paperColor)
        ) {
            // Book Spine Central Shadow Effect
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .width(16.dp)
                    .align(Alignment.CenterStart)
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(Color(0x33000000), Color.Transparent)
                        )
                    )
            )

            // Page Content with 3D Rotation Animation
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp)
                    .graphicsLayer {
                        rotationY = animatedAngle
                        cameraDistance = 12 * density
                    }
                    .verticalScroll(rememberScrollState())
            ) {
                // Header (Book Title & Part Number)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = book.title.uppercase(),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = selectedStyle.accentColor,
                        maxLines = 1
                    )
                    Text(
                        text = "Parte ${currentPartIndex + 1} / ${book.partsCount}",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = selectedStyle.accentColor
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Text Content
                Text(
                    text = textPart.ifEmpty { "Cargando texto de la página..." },
                    fontSize = fontSizeSp.sp,
                    fontFamily = if (isSerifFont) FontFamily.Serif else FontFamily.Default,
                    lineHeight = (fontSizeSp * 1.6).sp,
                    color = selectedStyle.textColor,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(32.dp))

                // Footer Page Number
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "- ${currentPartIndex + 1} -",
                        fontSize = 12.sp,
                        color = selectedStyle.accentColor,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // Page Flip Navigation Buttons
            IconButton(
                onClick = {
                    flipAngle = -30f
                    onPreviousPart()
                    flipAngle = 0f
                },
                modifier = Modifier
                    .align(Alignment.CenterStart)
                    .padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateBefore, contentDescription = "Página anterior", tint = selectedStyle.textColor)
            }

            IconButton(
                onClick = {
                    flipAngle = 30f
                    onNextPart()
                    flipAngle = 0f
                },
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .padding(4.dp)
                    .background(Color(0x22000000), RoundedCornerShape(16.dp))
            ) {
                Icon(Icons.Default.NavigateNext, contentDescription = "Siguiente página", tint = selectedStyle.textColor)
            }
        }
    }
}
