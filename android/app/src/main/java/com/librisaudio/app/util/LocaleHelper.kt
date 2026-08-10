package com.librisaudio.app.util

import android.content.Context
import android.content.res.Configuration
import java.util.Locale

/**
 * Cambio de idioma por-app (i18n). Envuelve el Context base con el locale elegido
 * en `attachBaseContext`, así funciona en TODAS las versiones (minSdk 24) sin
 * depender de AppCompatActivity ni de Google Play Services.
 * Valores: "system" (sigue el idioma del teléfono), "es", "en".
 */
object LocaleHelper {
    private const val PREF = "libris_prefs"
    private const val KEY = "app_lang"

    fun getLang(context: Context): String =
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString(KEY, "system") ?: "system"

    fun setLang(context: Context, tag: String) {
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY, tag).apply()
    }

    /** Envuelve el Context con el idioma elegido (o el del sistema si es "system"). */
    fun wrap(base: Context): Context {
        val tag = getLang(base)
        if (tag == "system") return base
        val locale = Locale.forLanguageTag(tag)
        Locale.setDefault(locale)
        val config = Configuration(base.resources.configuration)
        config.setLocale(locale)
        return base.createConfigurationContext(config)
    }
}
