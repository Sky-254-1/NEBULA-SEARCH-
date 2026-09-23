package com.nebula.search

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.webkit.*
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.webkit.WebViewAssetLoader
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.Executor

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var executor: Executor
    private lateinit var biometricPrompt: BiometricPrompt
    private lateinit var promptInfo: BiometricPrompt.PromptInfo

    private val apiBaseUrl = "http://10.0.2.2:8000" // Android emulator → host localhost

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        setupWebView()
        setupBiometric()
        setupJavascriptInterface()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = true
            displayZoomControls = false
            mediaPlaybackRequiresUserGesture = false
            javaScriptCanOpenWindowsAutomatically = true
            setSupportZoom(true)
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString() ?: return false
                return handleUrl(url)
            }

            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                return handleUrl(url ?: return false)
            }
        }

        webView.webChromeClient = WebChromeClient()

        // Load the frontend (dev server or local assets)
        val devUrl = "http://10.0.2.2:5173"
        webView.loadUrl(devUrl)

        // Register FCM token if available
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                task.result?.let { token ->
                    webView.post {
                        webView.evaluateJavascript(
                            "window.dispatchEvent(new CustomEvent('fcm-token', { detail: '${token.replace("'", "\\'")}' }));",
                            null
                        )
                    }
                }
            }
        }
    }

    private fun handleUrl(url: String): Boolean {
        return when {
            url.startsWith(apiBaseUrl) -> {
                webView.loadUrl(url)
                true
            }
            url.startsWith("http://10.0.2.2:5173") -> {
                webView.loadUrl(url)
                true
            }
            url.startsWith("http://") || url.startsWith("https://") -> {
                // Open external links in browser
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                true
            }
            else -> false
        }
    }

    private fun setupBiometric() {
        executor = ContextCompat.getMainExecutor(this)
        biometricPrompt = BiometricPrompt(this, executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    // Inject auth success into WebView
                    webView.evaluateJavascript(
                        "window.dispatchEvent(new CustomEvent('biometric-auth-success'));",
                        null
                    )
                    Toast.makeText(this@MainActivity, "Biometric verified", Toast.LENGTH_SHORT).show()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    Toast.makeText(this@MainActivity, "Auth error: $errString", Toast.LENGTH_SHORT).show()
                }

                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    Toast.makeText(this@MainActivity, "Auth failed", Toast.LENGTH_SHORT).show()
                }
            })

        promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Nebula Search")
            .setSubtitle("Authenticate to continue")
            .setNegativeButtonText("Cancel")
            .build()
    }

    private fun setupJavascriptInterface() {
        webView.addJavascriptInterface(object {
            @android.webkit.JavascriptInterface
            fun getApiBaseUrl(): String = apiBaseUrl

            @android.webkit.JavascriptInterface
            fun isBiometricAvailable(): Boolean {
                val manager = BiometricManager.from(this@MainActivity)
                return manager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG) ==
                    BiometricManager.BIOMETRIC_SUCCESS
            }

            @android.webkit.JavascriptInterface
            fun authenticate() {
                runOnUiThread {
                    if (isBiometricAvailable()) {
                        biometricPrompt.authenticate(promptInfo)
                    } else {
                        Toast.makeText(this@MainActivity, "Biometric not available", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            @android.webkit.JavascriptInterface
            fun getPlatform(): String = "android"
        }, "NebulaBridge")
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}