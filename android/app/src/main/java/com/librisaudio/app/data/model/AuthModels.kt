package com.librisaudio.app.data.model

data class AppwriteSession(
    val userId: String,
    val email: String,
    val name: String,
    val sessionId: String
)

data class AppwriteUserResponse(
    val `$id`: String,
    val email: String,
    val name: String
)

data class AppwriteSessionResponse(
    val `$id`: String,
    val userId: String
)

data class AppwriteEmailLoginBody(
    val email: String,
    val password: String
)

data class AppwriteRegisterBody(
    val userId: String,
    val email: String,
    val password: String,
    val name: String
)
