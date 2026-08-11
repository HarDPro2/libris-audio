package com.librisaudio.app.data.model

/** Una voz neural de Edge TTS (Microsoft Azure). */
data class TtsVoice(
    val id: String,        // ID de Edge TTS, p.ej. "es-MX-JorgeNeural"
    val name: String,      // nombre para mostrar
    val country: String,   // país (dato)
    val female: Boolean,   // género (se localiza en la UI)
    val flag: String,      // emoji de bandera
    val english: Boolean = false  // true = voz en inglés
)

object VoiceCatalog {
    const val DEFAULT = "es-MX-JorgeNeural"
    const val DEFAULT_EN = "en-US-AriaNeural"

    val voices = listOf(
        // ── Español (Latinoamérica + España) ──
        TtsVoice("es-AR-ElenaNeural",     "Elena",     "Argentina",      true,  "🇦🇷"),
        TtsVoice("es-AR-TomasNeural",     "Tomás",     "Argentina",      false, "🇦🇷"),
        TtsVoice("es-BO-SofiaNeural",     "Sofía",     "Bolivia",        true,  "🇧🇴"),
        TtsVoice("es-BO-MarceloNeural",   "Marcelo",   "Bolivia",        false, "🇧🇴"),
        TtsVoice("es-CL-CatalinaNeural",  "Catalina",  "Chile",          true,  "🇨🇱"),
        TtsVoice("es-CL-LorenzoNeural",   "Lorenzo",   "Chile",          false, "🇨🇱"),
        TtsVoice("es-CO-SalomeNeural",    "Salomé",    "Colombia",       true,  "🇨🇴"),
        TtsVoice("es-CO-GonzaloNeural",   "Gonzalo",   "Colombia",       false, "🇨🇴"),
        TtsVoice("es-CR-MariaNeural",     "María",     "Costa Rica",     true,  "🇨🇷"),
        TtsVoice("es-CR-JuanNeural",      "Juan",      "Costa Rica",     false, "🇨🇷"),
        TtsVoice("es-CU-BelkysNeural",    "Belkys",    "Cuba",           true,  "🇨🇺"),
        TtsVoice("es-CU-ManuelNeural",    "Manuel",    "Cuba",           false, "🇨🇺"),
        TtsVoice("es-DO-RamonaNeural",    "Ramona",    "Rep. Dominicana",true,  "🇩🇴"),
        TtsVoice("es-DO-EmilioNeural",    "Emilio",    "Rep. Dominicana",false, "🇩🇴"),
        TtsVoice("es-EC-AndreaNeural",    "Andrea",    "Ecuador",        true,  "🇪🇨"),
        TtsVoice("es-EC-LuisNeural",      "Luis",      "Ecuador",        false, "🇪🇨"),
        TtsVoice("es-ES-ElviraNeural",    "Elvira",    "España",         true,  "🇪🇸"),
        TtsVoice("es-ES-AlvaroNeural",    "Álvaro",    "España",         false, "🇪🇸"),
        TtsVoice("es-GT-MartaNeural",     "Marta",     "Guatemala",      true,  "🇬🇹"),
        TtsVoice("es-GT-AndresNeural",    "Andrés",    "Guatemala",      false, "🇬🇹"),
        TtsVoice("es-HN-KarlaNeural",     "Karla",     "Honduras",       true,  "🇭🇳"),
        TtsVoice("es-HN-CarlosNeural",    "Carlos",    "Honduras",       false, "🇭🇳"),
        TtsVoice("es-MX-DaliaNeural",     "Dalia",     "México",         true,  "🇲🇽"),
        TtsVoice("es-MX-JorgeNeural",     "Jorge",     "México",         false, "🇲🇽"),
        TtsVoice("es-NI-YolandaNeural",   "Yolanda",   "Nicaragua",      true,  "🇳🇮"),
        TtsVoice("es-NI-FedericoNeural",  "Federico",  "Nicaragua",      false, "🇳🇮"),
        TtsVoice("es-PA-MargaritaNeural", "Margarita", "Panamá",         true,  "🇵🇦"),
        TtsVoice("es-PA-RobertoNeural",   "Roberto",   "Panamá",         false, "🇵🇦"),
        TtsVoice("es-PE-CamilaNeural",    "Camila",    "Perú",           true,  "🇵🇪"),
        TtsVoice("es-PE-AlexNeural",      "Alex",      "Perú",           false, "🇵🇪"),
        TtsVoice("es-PR-KarinaNeural",    "Karina",    "Puerto Rico",    true,  "🇵🇷"),
        TtsVoice("es-PR-VictorNeural",    "Víctor",    "Puerto Rico",    false, "🇵🇷"),
        TtsVoice("es-PY-TaniaNeural",     "Tania",     "Paraguay",       true,  "🇵🇾"),
        TtsVoice("es-PY-MarioNeural",     "Mario",     "Paraguay",       false, "🇵🇾"),
        TtsVoice("es-SV-LorenaNeural",    "Lorena",    "El Salvador",    true,  "🇸🇻"),
        TtsVoice("es-SV-RodrigoNeural",   "Rodrigo",   "El Salvador",    false, "🇸🇻"),
        TtsVoice("es-US-PalomaNeural",    "Paloma",    "EE.UU. (Latino)",true,  "🇺🇸"),
        TtsVoice("es-US-AlonsoNeural",    "Alonso",    "EE.UU. (Latino)",false, "🇺🇸"),
        TtsVoice("es-UY-ValentinaNeural", "Valentina", "Uruguay",        true,  "🇺🇾"),
        TtsVoice("es-UY-MateoNeural",     "Mateo",     "Uruguay",        false, "🇺🇾"),
        TtsVoice("es-VE-PaolaNeural",     "Paola",     "Venezuela",      true,  "🇻🇪"),
        TtsVoice("es-VE-SebastianNeural", "Sebastián", "Venezuela",      false, "🇻🇪"),

        // ── English ──
        TtsVoice("en-US-AriaNeural",        "Aria",        "USA",          true,  "🇺🇸", english = true),
        TtsVoice("en-US-JennyNeural",       "Jenny",       "USA",          true,  "🇺🇸", english = true),
        TtsVoice("en-US-MichelleNeural",    "Michelle",    "USA",          true,  "🇺🇸", english = true),
        TtsVoice("en-US-AnaNeural",         "Ana",         "USA",          true,  "🇺🇸", english = true),
        TtsVoice("en-US-GuyNeural",         "Guy",         "USA",          false, "🇺🇸", english = true),
        TtsVoice("en-US-EricNeural",        "Eric",        "USA",          false, "🇺🇸", english = true),
        TtsVoice("en-US-ChristopherNeural", "Christopher", "USA",          false, "🇺🇸", english = true),
        TtsVoice("en-US-RogerNeural",       "Roger",       "USA",          false, "🇺🇸", english = true),
        TtsVoice("en-US-SteffanNeural",     "Steffan",     "USA",          false, "🇺🇸", english = true),
        TtsVoice("en-GB-SoniaNeural",       "Sonia",       "UK",           true,  "🇬🇧", english = true),
        TtsVoice("en-GB-LibbyNeural",       "Libby",       "UK",           true,  "🇬🇧", english = true),
        TtsVoice("en-GB-RyanNeural",        "Ryan",        "UK",           false, "🇬🇧", english = true),
        TtsVoice("en-GB-ThomasNeural",      "Thomas",      "UK",           false, "🇬🇧", english = true),
        TtsVoice("en-AU-NatashaNeural",     "Natasha",     "Australia",    true,  "🇦🇺", english = true),
        TtsVoice("en-AU-WilliamNeural",     "William",     "Australia",    false, "🇦🇺", english = true),
        TtsVoice("en-CA-ClaraNeural",       "Clara",       "Canada",       true,  "🇨🇦", english = true),
        TtsVoice("en-CA-LiamNeural",        "Liam",        "Canada",       false, "🇨🇦", english = true),
        TtsVoice("en-IE-EmilyNeural",       "Emily",       "Ireland",      true,  "🇮🇪", english = true),
        TtsVoice("en-IE-ConnorNeural",      "Connor",      "Ireland",      false, "🇮🇪", english = true),
        TtsVoice("en-IN-NeerjaNeural",      "Neerja",      "India",        true,  "🇮🇳", english = true),
        TtsVoice("en-IN-PrabhatNeural",     "Prabhat",     "India",        false, "🇮🇳", english = true)
    )

    fun byId(id: String): TtsVoice? = voices.firstOrNull { it.id == id }
}
