package com.librisaudio.app.util

import android.content.Context
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily

/**
 * Resolver UNIVERSAL de fuentes artísticas embebidas.
 * Cumple DIRECTIVA_FUENTES_ARTISTICAS_EMBEBIDAS (obligatoria Android + Windows):
 * usa el archivo `<name>.ttf` de `res/font/` si existe, con caída ELEGANTE a una
 * familia integrada de Android si faltara. Nunca depende de red ni de Google
 * Play Services (Downloadable Fonts).
 *
 * Reutilizable tal cual en cualquier proyecto Android. Para Compose Multiplatform
 * (Windows/Desktop) el equivalente es `FontFamily(Font(Res.font.<name>))` sobre
 * las mismas .ttf en `composeResources/font/`.
 */
object ArtisticFonts {

    /** Fuente embebida por nombre de recurso, con fallback obligatorio. */
    fun resolve(ctx: Context, name: String, fallback: FontFamily): FontFamily {
        val resId = ctx.resources.getIdentifier(name, "font", ctx.packageName)
        return if (resId != 0) FontFamily(Font(resId)) else fallback
    }
}
