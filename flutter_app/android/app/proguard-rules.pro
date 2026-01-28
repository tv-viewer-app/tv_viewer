# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Video Player - ExoPlayer
-keep class com.google.android.exoplayer2.** { *; }
-keep interface com.google.android.exoplayer2.** { *; }
-dontwarn com.google.android.exoplayer2.**

# HTTP Client (OkHttp - used by video_player and http package)
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }

# URL Launcher
-keep class io.flutter.plugins.urllauncher.** { *; }

# Shared Preferences
-keep class io.flutter.plugins.sharedpreferences.** { *; }

# Path Provider
-keep class io.flutter.plugins.pathprovider.** { *; }

# Prevent stripping of native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep Kotlin metadata
-keep class kotlin.Metadata { *; }
-keepclassmembers class ** {
    @kotlin.Metadata *;
}

# Keep Google Fonts (if used)
-keep class com.google.fonts.** { *; }

# Wakelock Plus
-keep class com.ryanheise.wakelock_plus.** { *; }
-keep class androidx.core.app.NotificationCompat { *; }

# Floating (PiP)
-keep class floating.** { *; }
-keep class io.flutter.plugins.floating.** { *; }

# Keep Provider classes
-keep class * extends androidx.lifecycle.ViewModel { *; }
-keep class * extends androidx.lifecycle.AndroidViewModel { *; }

# Prevent obfuscation of model classes (JSON serialization)
-keepclassmembers class com.tvviewer.app.** {
    <init>(...);
    <fields>;
}

# Crashlytics (if added later)
-keepattributes SourceFile,LineNumberTable
-keep public class * extends java.lang.Exception

# General Android
-keep class androidx.** { *; }
-keep interface androidx.** { *; }

# Remove logging in release (optional - reduces APK size)
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# Keep R8 compatible
-dontwarn org.bouncycastle.**
-dontwarn org.conscrypt.**
-dontwarn org.openjsse.**
