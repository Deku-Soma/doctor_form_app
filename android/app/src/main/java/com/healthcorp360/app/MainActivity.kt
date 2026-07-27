package com.healthcorp360.app

import android.os.Bundle
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.LinearLayout
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var loadingLayout: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 1. Initialize Chaquopy Python Runtime
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webview)
        loadingLayout = findViewById(R.id.loading_layout)

        // 2. Generate Shared Secret and Set Environment Variables for Python
        val secret = UUID.randomUUID().toString()
        val outputDir = filesDir.absolutePath

        System.setProperty("HC360_APP_SECRET", secret)
        System.setProperty("HC360_OUTPUT_DIR", outputDir)

        // 3. Configure WebView Settings
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = false
        webView.settings.allowContentAccess = false

        // 4. Start Python Server in Background Thread
        Thread {
            try {
                val py = Python.getInstance()
                py.getModule("main_server").callAttr("run_server")
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()

        // 5. Poll /health endpoint, then show WebView
        Thread {
            waitForServer()
            runOnUiThread {
                webView.webViewClient = SecretInjectingClient(secret)
                loadingLayout.visibility = View.GONE
                webView.visibility = View.VISIBLE
                webView.loadUrl("http://127.0.0.1:8765")
            }
        }.start()
    }

    private fun waitForServer() {
        repeat(80) { // Max 8 seconds (80 * 100ms)
            try {
                val conn = URL("http://127.0.0.1:8765/health").openConnection() as HttpURLConnection
                conn.connectTimeout = 500
                if (conn.responseCode == 200) return
            } catch (_: Exception) {}
            Thread.sleep(100)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}

class SecretInjectingClient(private val secret: String) : WebViewClient() {
    override fun onPageFinished(view: WebView, url: String) {
        super.onPageFinished(view, url)
        view.evaluateJavascript("window.__APP_SECRET__ = '$secret';", null)
    }
}
