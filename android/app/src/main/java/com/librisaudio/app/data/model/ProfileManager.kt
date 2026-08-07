package com.librisaudio.app.data.model

import android.content.Context

/** Perfil local del usuario: nombre para mostrar, avatar elegido y/o foto personal. */
data class UserProfile(
    val displayName: String = "",
    val avatarId: Int = 0,
    val photoUri: String = ""   // si no está vacío, se usa la foto en vez del avatar
)

object ProfileManager {
    private const val PREFS = "libris_profile"

    fun load(context: Context): UserProfile {
        val p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return UserProfile(
            displayName = p.getString("display_name", "") ?: "",
            avatarId    = p.getInt("avatar_id", 0),
            photoUri    = p.getString("photo_uri", "") ?: ""
        )
    }

    fun save(context: Context, profile: UserProfile) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString("display_name", profile.displayName)
            .putInt("avatar_id", profile.avatarId)
            .putString("photo_uri", profile.photoUri)
            .apply()
    }
}
