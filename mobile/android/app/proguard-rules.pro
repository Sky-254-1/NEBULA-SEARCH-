# Keep WebView JavaScript interface methods
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep Firebase Messaging
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**