package com.librisaudio.app.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.PictureAsPdf
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
import com.librisaudio.app.data.model.BookCategories
import com.librisaudio.app.ui.components.AnimatedBackground
import com.librisaudio.app.ui.theme.AppThemePreset
import com.librisaudio.app.ui.theme.TextMuted
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

@Composable
fun UploadScreen(
    currentTheme: AppThemePreset,
    currentUserId: String,
    onUploadSuccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var bookTitle by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf("") }
    var showCategoryDropdown by remember { mutableStateOf(false) }
    var isUploading by remember { mutableStateOf(false) }
    var uploadProgress by remember { mutableStateOf("") }
    var uploadSuccess by remember { mutableStateOf(false) }
    var uploadError by remember { mutableStateOf("") }

    val pdfLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedUri = uri
        uploadSuccess = false
        uploadError = ""
        if (uri != null && bookTitle.isBlank()) {
            // Auto-fill title from filename
            val cursor = context.contentResolver.query(uri, null, null, null, null)
            cursor?.use {
                val nameIndex = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                it.moveToFirst()
                val fileName = it.getString(nameIndex) ?: "libro.pdf"
                bookTitle = fileName.removeSuffix(".pdf").replace("_", " ").replace("-", " ").trim()
            }
        }
    }

    // Form validation
    val canUpload = selectedUri != null && bookTitle.isNotBlank() && selectedCategory.isNotBlank() && !isUploading

    Box(modifier = modifier.fillMaxSize()) {
        AnimatedBackground(preset = currentTheme)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(8.dp))

            // Header
            Icon(
                imageVector = Icons.Default.CloudUpload,
                contentDescription = null,
                tint = currentTheme.primary,
                modifier = Modifier.size(52.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text("Subir Audiolibro", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Text("Convierte un PDF en audio neuronal", fontSize = 13.sp, color = TextMuted)

            Spacer(modifier = Modifier.height(24.dp))

            // PDF picker card
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(18.dp))
                    .background(Color(0x441E293B))
                    .clickable { pdfLauncher.launch("application/pdf") }
                    .padding(24.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = if (selectedUri != null) Icons.Default.PictureAsPdf else Icons.Default.CloudUpload,
                        contentDescription = null,
                        tint = if (selectedUri != null) currentTheme.secondary else currentTheme.primary,
                        modifier = Modifier.size(42.dp)
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    if (selectedUri != null) {
                        Text("✓ PDF seleccionado", color = currentTheme.secondary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text(
                            text = selectedUri!!.lastPathSegment ?: "archivo.pdf",
                            color = TextMuted,
                            fontSize = 12.sp
                        )
                    } else {
                        Text("Toca para seleccionar un PDF", color = Color.White, fontSize = 14.sp)
                        Text("Solo archivos PDF con texto extraíble", color = TextMuted, fontSize = 12.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Title field (obligatorio)
            OutlinedTextField(
                value = bookTitle,
                onValueChange = { bookTitle = it },
                label = {
                    Text(
                        "Título del libro *",
                        color = if (bookTitle.isBlank()) Color(0xFFEF4444) else TextMuted
                    )
                },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = currentTheme.primary,
                    unfocusedBorderColor = if (bookTitle.isBlank()) Color(0x44EF4444) else Color(0x44FFFFFF),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Category selector (obligatorio)
            Box(modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    value = selectedCategory.ifBlank { "" },
                    onValueChange = {},
                    readOnly = true,
                    label = {
                        Text(
                            "Categoría *",
                            color = if (selectedCategory.isBlank()) Color(0xFFEF4444) else TextMuted
                        )
                    },
                    placeholder = { Text("Selecciona una categoría", color = TextMuted) },
                    trailingIcon = {
                        Icon(Icons.Default.ArrowDropDown, contentDescription = null, tint = TextMuted)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { showCategoryDropdown = true },
                    shape = RoundedCornerShape(14.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = currentTheme.primary,
                        unfocusedBorderColor = if (selectedCategory.isBlank()) Color(0x44EF4444) else Color(0x44FFFFFF),
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    )
                )
                DropdownMenu(
                    expanded = showCategoryDropdown,
                    onDismissRequest = { showCategoryDropdown = false },
                    modifier = Modifier
                        .fillMaxWidth(0.9f)
                        .background(Color(0xFF1E293B))
                ) {
                    BookCategories.ALL.forEach { cat ->
                        DropdownMenuItem(
                            text = { Text(cat, color = Color.White) },
                            onClick = {
                                selectedCategory = cat
                                showCategoryDropdown = false
                            }
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Upload button
            if (isUploading) {
                CircularProgressIndicator(color = currentTheme.primary)
                Spacer(modifier = Modifier.height(8.dp))
                Text(uploadProgress, color = TextMuted, fontSize = 13.sp)
            } else {
                Button(
                    onClick = {
                        val uri = selectedUri ?: return@Button
                        isUploading = true
                        uploadProgress = "Preparando archivo…"
                        uploadError = ""
                        uploadSuccess = false

                        coroutineScope.launch(Dispatchers.IO) {
                            try {
                                withContext(Dispatchers.Main) { uploadProgress = "Subiendo al servidor…" }

                                val inputStream = context.contentResolver.openInputStream(uri)
                                val bytes = inputStream?.readBytes() ?: ByteArray(0)
                                inputStream?.close()

                                val filePart = MultipartBody.Part.createFormData(
                                    "file",
                                    "documento.pdf",
                                    bytes.toRequestBody("application/pdf".toMediaTypeOrNull())
                                )
                                val titleBody = bookTitle.trim().toRequestBody("text/plain".toMediaTypeOrNull())
                                val categoryBody = selectedCategory.toRequestBody("text/plain".toMediaTypeOrNull())
                                val addedByBody = currentUserId.toRequestBody("text/plain".toMediaTypeOrNull())

                                val response = ApiClient.backendService.uploadPdf(
                                    filePart, titleBody, categoryBody, addedByBody
                                )

                                withContext(Dispatchers.Main) {
                                    isUploading = false
                                    if (response.isSuccessful) {
                                        uploadSuccess = true
                                        uploadProgress = ""
                                        selectedUri = null
                                        bookTitle = ""
                                        selectedCategory = ""
                                        onUploadSuccess()
                                    } else {
                                        uploadError = "Error del servidor: ${response.code()}"
                                    }
                                }
                            } catch (e: Exception) {
                                withContext(Dispatchers.Main) {
                                    isUploading = false
                                    uploadError = "Error: ${e.localizedMessage}"
                                }
                            }
                        }
                    },
                    enabled = canUpload,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = currentTheme.primary,
                        disabledContainerColor = Color(0x44FFFFFF)
                    )
                ) {
                    Icon(Icons.Default.CloudUpload, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "Procesar y convertir a audiolibro",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                }

                if (!canUpload && selectedUri != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = buildString {
                            if (bookTitle.isBlank()) append("• El título es obligatorio\n")
                            if (selectedCategory.isBlank()) append("• Selecciona una categoría")
                        }.trim(),
                        color = Color(0xFFEF4444),
                        fontSize = 12.sp
                    )
                }
            }

            // Feedback
            if (uploadSuccess) {
                Spacer(modifier = Modifier.height(16.dp))
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFF10B981).copy(alpha = 0.15f)
                ) {
                    Text(
                        "✓ ¡Libro procesado con éxito! Ya está disponible en el catálogo.",
                        color = Color(0xFF10B981),
                        modifier = Modifier.padding(12.dp),
                        fontSize = 13.sp
                    )
                }
            }
            if (uploadError.isNotBlank()) {
                Spacer(modifier = Modifier.height(16.dp))
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFFEF4444).copy(alpha = 0.12f)
                ) {
                    Text(
                        uploadError,
                        color = Color(0xFFEF4444),
                        modifier = Modifier.padding(12.dp),
                        fontSize = 13.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(80.dp))
        }
    }
}
