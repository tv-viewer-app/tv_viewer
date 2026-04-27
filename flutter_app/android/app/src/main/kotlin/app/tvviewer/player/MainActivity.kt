package app.tvviewer.player

import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest

class MainActivity: FlutterActivity() {
    private val CHANNEL = "tv_viewer/intent"
    private val INTEGRITY_CHANNEL = "tv_viewer/integrity"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Video player intent channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "openInVideoPlayer" -> {
                    val url = call.argument<String>("url") ?: ""
                    val title = call.argument<String>("title") ?: ""
                    val targetPackage = call.argument<String>("package")
                    try {
                        val intent = Intent(Intent.ACTION_VIEW).apply {
                            setDataAndType(Uri.parse(url), "video/*")
                            putExtra("title", title)
                            putExtra(Intent.EXTRA_TITLE, title)
                            if (targetPackage != null) {
                                setPackage(targetPackage)
                            }
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        if (intent.resolveActivity(packageManager) != null) {
                            startActivity(intent)
                            result.success(true)
                        } else if (targetPackage != null) {
                            intent.setPackage(null)
                            val chooser = Intent.createChooser(intent, "Open with")
                            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            startActivity(chooser)
                            result.success(true)
                        } else {
                            result.success(false)
                        }
                    } catch (e: Exception) {
                        result.error("INTENT_ERROR", e.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }

        // Play Integrity API channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, INTEGRITY_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "requestIntegrityToken" -> {
                    val nonce = call.argument<String>("nonce")
                    if (nonce == null) {
                        result.error("INVALID_NONCE", "Nonce is required", null)
                        return@setMethodCallHandler
                    }
                    try {
                        val integrityManager = IntegrityManagerFactory.create(applicationContext)
                        val request = IntegrityTokenRequest.builder()
                            .setNonce(nonce)
                            .build()
                        integrityManager.requestIntegrityToken(request)
                            .addOnSuccessListener { response ->
                                result.success(response.token())
                            }
                            .addOnFailureListener { e ->
                                result.error("INTEGRITY_ERROR", e.message, e.toString())
                            }
                    } catch (e: Exception) {
                        result.error("INTEGRITY_INIT_ERROR", e.message, e.toString())
                    }
                }
                else -> result.notImplemented()
            }
        }
    }
}


