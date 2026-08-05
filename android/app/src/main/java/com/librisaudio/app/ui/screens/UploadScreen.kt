package com.librisaudio.app.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.librisaudio.app.data.api.ApiClient
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

@Composable
fun UploadScreen(
    currentTheme: AppThemePreset,
    onUploadSuccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var bookTitle by remember { mutableStateOf("") }
    var isUploading by remember { mutableStateOf(false) }
    var uploadStatus by remember { mutableStateOf("") }

    val pdfLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedUri = uri
        if (uri != null) {
            val fileName = uri.lastPathSegment ?: "Libro.pdf"
            if (bookTitle.isEmpty()) {
                bookTitle = fileName.replace(".pdf", "", ignoreCase = true)
            }
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Subir Libro PDF",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )

            Text(
                text = "Convierte cualquier documento PDF en un audiolibro neuronal",
                fontSize = 12.sp,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Upload Card Dropzone
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .clip(RoundedCornerShape(20.dp))
                    .background(Color(0x331E293B))
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.CloudUpload,
                        contentDescription = null,
                        tint = currentTheme.primary,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = if (selectedUri != null) "PDF Seleccionado: ${selectedUri?.lastPathSegment}" else "Seleccionar archivo PDF",
                        color = Color.White,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { pdfLauncher.launch("application/pdf") },
                        colors = ButtonDefaults.buttonColors(containerColor = currentTheme.primary)
                    ) {
                        Text(if (selectedUri != null) "Cambiar PDF" else "Examinar Archivos")
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            OutlinedTextField(
                value = bookTitle,
                onValueChange = { bookTitle = it },
                label = { Text("Título del Libro", color = TextMuted) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = currentTheme.primary,
                    unfocusedBorderColor = Color(0x44FFFFFF),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(20.dp))

            if (isUploading) {
                CircularProgressIndicator(color = currentTheme.primary)
                Spacer(modifier = Modifier.height(8.dp))
                Text(uploadStatus, color = Color.White, fontSize = 12.sp)
            } else {
                Button(
                    onClick = {
                        val uri = selectedUri ?: return@Button
                        isUploading = true
                        uploadStatus = "Procesando PDF en Google Cloud Run..."
                        coroutineScope.launch(Dispatchers.IO) {
                            try {
                                val contentResolver = context.contentResolver
                                val inputStream = contentResolver.openInputStream(uri)
                                val bytes = inputStream?.readBytes() ?: ByteArray(0)
                                inputStream?.close()

                                val requestBody = MultipartBody.Builder()
                                    .setType(MultipartBody.FORM)
                                    .addFormDataPart(
                                        "file",
                                        "document.pdf",
                                        bytes.toRequestBody("application/pdf".toMediaTypeOrNull())
                                    )
                                    .addFormDataPart("title", bookTitle.ifEmpty { "Nuevo Libro" })
                                    .build()

                                val request = Request.Builder()
                                    .url("${ApiClient.BACKEND_URL}api/upload-pdf")
                                    .post(requestBody)
                                    .build()

                                val client = OkHttpClient()
                                val response = client.newCall(request).execute()

                                withContext(Dispatchers.Main) {
                                    isUploading = false
                                    if (response.isSuccessful) {
                                        uploadStatus = "¡Libro procesado con éxito!"
                                        onUploadSuccess()
                                    } else {
                                        uploadStatus = "Error en el servidor (${response.code})"
                                    }
                                }
                            } catch (e: Exception) {
                                withContext(Dispatchers.Main) {
                                    isUploading = false
                                    uploadStatus = "Error: ${e.localizedMessage}"
                                }
                            }
                        }
                    },
                    enabled = selectedUri != null && !isUploading,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = currentTheme.secondary)
                ) {
                    Text("Procesar y Convertir a Audiolibro")
                }
            }

            if (uploadStatus.isNotEmpty() && !isUploading) {
                Spacer(modifier = Modifier.height(12.dp))
                Text(uploadStatus, color = Color.Green, fontSize = 13.sp)
            }
        }
    }
}
