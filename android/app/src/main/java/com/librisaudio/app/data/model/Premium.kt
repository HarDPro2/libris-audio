package com.librisaudio.app.data.model

import android.content.Context

/**
 * Estado premium del usuario.
 *
 * Hoy es una preferencia local que se activa a mano: la monetización real
 * (META 5) llega después de la versión de Windows. Lo importante es que TODO
 * el código consulte solo aquí, así que cuando exista la suscripción de verdad
 * solo cambia el cuerpo de `isPremium` y no hay que buscar comprobaciones
 * repartidas por la app.
 */
object Premium {

    private const val PREFS = "libris_progress"
    private const val CLAVE = "premium_activo"

    /** Marcos incluidos en el plan gratuito. El resto exige premium. */
    val MARCOS_GRATIS = setOf(
        com.librisaudio.app.ui.components.BookBindingStyle.CLASSIC,
        com.librisaudio.app.ui.components.BookBindingStyle.MEDIEVAL,
    )

    fun isPremium(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(CLAVE, false)

    fun setPremium(context: Context, activo: Boolean) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(CLAVE, activo).apply()
    }

    /** ¿Puede este usuario usar el marco 3D de este género? */
    fun marcoDisponible(
        context: Context,
        estilo: com.librisaudio.app.ui.components.BookBindingStyle
    ): Boolean = estilo in MARCOS_GRATIS || isPremium(context)
}
