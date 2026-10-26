package org.credium.app

/**
 * The one place the demo URL lives.
 *
 * Quick tunnels rotate their hostname on every cloudflared restart, so if you
 * restart the tunnel, update this constant and rebuild — or (better) switch to a
 * named tunnel and pin a stable hostname here.
 */
object Config {
    /** Cloudflare quick tunnel to the demo host (Ayaan's laptop). */
    const val DEMO_URL = "https://gray-companies-participation-twin.trycloudflare.com/app/"

    /** Fallback when the phone is on the same Wi-Fi as the demo host. */
    const val LAN_URL = "http://10.145.46.52:8000"
}
