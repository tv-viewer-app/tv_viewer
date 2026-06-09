package app.tvviewer.player

import android.content.Intent
import android.net.Uri
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CHANNEL = "tv_viewer/intent"
    private val WAKELOCK_CHANNEL = "tv_viewer/wakelock"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Screen wake lock channel — uses FLAG_KEEP_SCREEN_ON (most reliable on Android 14+)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, WAKELOCK_CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "enable" -> {
                    runOnUiThread {
                        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    }
                    result.success(true)
                }
                "disable" -> {
                    runOnUiThread {
                        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    }
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }

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

    }
}

