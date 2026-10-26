package org.credium.app

import android.annotation.SuppressLint
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

/**
 * Full-screen WebView around the Credium demo page.
 *
 * The backend is the same FastAPI + anvil stack that runs on the demo host, so
 * nothing here re-implements product logic: it loads the real page and the real
 * buttons. Swipe down to refresh. If the tunnel is down we show a retry screen
 * instead of a blank white rectangle.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var refresh: SwipeRefreshLayout
    private lateinit var offline: LinearLayout
    private lateinit var offlineDetail: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0f1720"))
        }

        web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            settings.mediaPlaybackRequiresUserGesture = false
            setBackgroundColor(Color.parseColor("#0f1720"))
        }

        refresh = SwipeRefreshLayout(this).apply {
            addView(
                web,
                LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.MATCH_PARENT
                )
            )
        }

        offline = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = android.view.Gravity.CENTER
            setBackgroundColor(Color.parseColor("#0f1720"))
            visibility = View.GONE
            setPadding(48, 48, 48, 48)
        }

        val offlineTitle = TextView(this).apply {
            text = "Demo host unreachable"
            setTextColor(Color.WHITE)
            textSize = 20f
        }
        offlineDetail = TextView(this).apply {
            text = Config.DEMO_URL
            setTextColor(Color.parseColor("#93a4b8"))
            textSize = 12f
            setPadding(0, 24, 0, 24)
        }
        val retry = Button(this).apply {
            text = "Retry"
            setOnClickListener { load() }
        }
        offline.addView(offlineTitle)
        offline.addView(offlineDetail)
        offline.addView(retry)

        root.addView(
            refresh,
            LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        )
        root.addView(
            offline,
            LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        )
        setContentView(root)

        refresh.setOnRefreshListener { load() }

        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                refresh.isRefreshing = false
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                // Only a failed main-frame load means the host is down; sub-resource
                // misses should not blank the page.
                if (request?.isForMainFrame == true) {
                    showOffline(error?.description?.toString() ?: "connection failed")
                }
            }
        }

        load()
    }

    private fun load() {
        offline.visibility = View.GONE
        web.visibility = View.VISIBLE
        refresh.isRefreshing = true
        web.loadUrl(Config.DEMO_URL)
    }

    private fun showOffline(reason: String) {
        refresh.isRefreshing = false
        offlineDetail.text = "${Config.DEMO_URL}\n\n$reason\n\nSame Wi-Fi? Try ${Config.LAN_URL}"
        offline.visibility = View.VISIBLE
        web.visibility = View.GONE
    }

    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }
}
