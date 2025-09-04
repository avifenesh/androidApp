package com.example.kidanimals

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.view.*
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2

class MainActivity : ComponentActivity() {

    private lateinit var pager: ViewPager2
    private lateinit var thumbs: RecyclerView
    private lateinit var exitBtn: ImageButton
    private var exitOverlay: ExitOverlayView? = null
    private val images: List<String> by lazy { loadAssetImages(this) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        pager = findViewById(R.id.pager)
        thumbs = findViewById(R.id.thumb_list)
        exitBtn = findViewById(R.id.btn_exit)

        pager.adapter = ImagePagerAdapter(this, images)
        // Optimize RecyclerView if items don't change size
        (pager.getChildAt(0) as? RecyclerView)?.setHasFixedSize(true)

        thumbs.layoutManager = LinearLayoutManager(this, RecyclerView.VERTICAL, false)
        val thumbAdapter = ThumbnailAdapter(this, images) { position ->
            pager.currentItem = position
        }
        thumbs.adapter = thumbAdapter
        // Optimize RecyclerView if items don't change size
        thumbs.setHasFixedSize(true)

        exitBtn.setOnLongClickListener {
            showExitOverlay()
            true
        }

        // Disable system back for kids unless overlay is up
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                // Ignore back to keep the kid in the app
            }
        })
    }

    override fun onResume() {
        super.onResume()
        tryStartLockTask()
    }

    private fun tryStartLockTask() {
        try {
            startLockTask()
        } catch (_: IllegalStateException) {
            // Ignore: not allowed in this mode
        } catch (_: SecurityException) {
            // Ignore: app not whitelisted; user can still pin manually
        }
    }

    private fun tryStopLockTask() {
        try {
            stopLockTask()
        } catch (_: Exception) {
            // In screen pinning, system handles unpin via gesture; show hint
            Toast.makeText(this, getString(R.string.unpin_instructions), Toast.LENGTH_LONG).show()
        }
    }

    private fun showExitOverlay() {
        if (exitOverlay != null) return
        val root = findViewById<ViewGroup>(android.R.id.content)
        val overlay = ExitOverlayView(this) {
            // Confirmed by swipe
            tryStopLockTask()
            finish()
        }
        root.addView(overlay, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        exitOverlay = overlay
    }

    private fun loadAssetImages(context: Context): List<String> {
        val dir = "animals"
        val files = context.assets.list(dir)?.toList().orEmpty()
            .filter {
                it.endsWith(".jpg", true) ||
                it.endsWith(".jpeg", true) ||
                it.endsWith(".png", true) ||
                it.endsWith(".webp", true)
            }
            .sorted()
        return files.map { "$dir/$it" }
    }
}

class ImagePagerAdapter(private val context: Context, private val assets: List<String>) : RecyclerView.Adapter<ImagePagerAdapter.Holder>() {
    class Holder(view: View) : RecyclerView.ViewHolder(view) {
        val image: ImageView = view.findViewById(R.id.full_image)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.pager_item_image, parent, false)
        return Holder(view)
    }

    override fun onBindViewHolder(holder: Holder, position: Int) {
        val assetPath = assets[position]
        holder.image.setImageBitmap(loadBitmapFromAssets(context, assetPath, maxDim = 1600))
    }

    override fun getItemCount(): Int = assets.size
}

class ThumbnailAdapter(
    private val context: Context,
    private val assets: List<String>,
    private val onClick: (Int) -> Unit
) : RecyclerView.Adapter<ThumbnailAdapter.Holder>() {

    inner class Holder(view: View) : RecyclerView.ViewHolder(view) {
        val thumb: ImageView = view.findViewById(R.id.thumb_image)
        init {
            view.setOnClickListener { onClick(bindingAdapterPosition) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_thumbnail, parent, false)
        return Holder(view)
    }

    override fun onBindViewHolder(holder: Holder, position: Int) {
        val assetPath = assets[position]
        holder.thumb.setImageBitmap(loadBitmapFromAssets(context, assetPath, maxDim = 240))
    }

    override fun getItemCount(): Int = assets.size
}

fun loadBitmapFromAssets(context: Context, assetPath: String, maxDim: Int): android.graphics.Bitmap? {
    return try {
        val am = context.assets
        am.open(assetPath).use { input ->
            // First decode bounds
            val opts = android.graphics.BitmapFactory.Options()
            opts.inJustDecodeBounds = true
            input.mark(Int.MAX_VALUE)
            android.graphics.BitmapFactory.decodeStream(input, null, opts)
            input.reset()

            val (w, h) = opts.outWidth to opts.outHeight
            var sample = 1
            var maxSide = maxOf(w, h)
            while (maxSide > maxDim) {
                sample *= 2
                maxSide /= 2
            }
            val opts2 = android.graphics.BitmapFactory.Options().apply { inSampleSize = sample }
            android.graphics.BitmapFactory.decodeStream(input, null, opts2)
        }
    } catch (_: Throwable) {
        null
    }
}

class ExitOverlayView(context: Context, private val onConfirmed: () -> Unit) : FrameLayout(context) {
    private var startY: Float = 0f
    private var handle: TextView
    private var container: View

    init {
        LayoutInflater.from(context).inflate(R.layout.overlay_exit, this, true)
        setOnClickListener { /* eat clicks */ }
        container = findViewById(R.id.swipe_container)
        handle = findViewById(R.id.swipe_handle)

        handle.setOnTouchListener { v, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    startY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dy = startY - event.rawY
                    // translate the handle up within the container bounds
                    val maxTravel = container.height - handle.height
                    val newTranslation = (dy).coerceIn(0f, maxTravel.toFloat())
                    handle.translationY = -newTranslation
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    val traveled = -handle.translationY
                    val threshold = container.height * 0.6f
                    if (traveled >= threshold) {
                        onConfirmed()
                    }
                    // Remove overlay regardless; parent can show again if needed
                    (parent as? ViewGroup)?.removeView(this)
                    true
                }
                else -> false
            }
        }
    }
}
