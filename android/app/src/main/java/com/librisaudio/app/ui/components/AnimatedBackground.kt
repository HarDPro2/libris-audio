package com.librisaudio.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import com.librisaudio.app.ui.theme.AppThemePreset

@Composable
fun AnimatedBackground(
    preset: AppThemePreset,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "BackgroundAnimation")

    val offset1 by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 15000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "Orb1"
    )

    val offset2 by infiniteTransition.animateFloat(
        initialValue = 360f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 20000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "Orb2"
    )

    val pColor = preset.primary.copy(alpha = 0.35f)
    val sColor = preset.secondary.copy(alpha = 0.25f)
    val bColor = preset.background

    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height

        // Base dark background
        drawRect(color = bColor)

        // Floating Orb 1 (Primary Color)
        val rad1 = Math.toRadians(offset1.toDouble())
        val orb1X = (width * 0.3f) + (Math.cos(rad1) * width * 0.25f).toFloat()
        val orb1Y = (height * 0.3f) + (Math.sin(rad1) * height * 0.2f).toFloat()

        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(pColor, Color.Transparent),
                center = Offset(orb1X, orb1Y),
                radius = width * 0.7f
            ),
            radius = width * 0.7f,
            center = Offset(orb1X, orb1Y)
        )

        // Floating Orb 2 (Secondary Color)
        val rad2 = Math.toRadians(offset2.toDouble())
        val orb2X = (width * 0.7f) + (Math.sin(rad2) * width * 0.3f).toFloat()
        val orb2Y = (height * 0.7f) + (Math.cos(rad2) * height * 0.25f).toFloat()

        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(sColor, Color.Transparent),
                center = Offset(orb2X, orb2Y),
                radius = width * 0.8f
            ),
            radius = width * 0.8f,
            center = Offset(orb2X, orb2Y)
        )
    }
}
