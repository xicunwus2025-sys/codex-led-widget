from pathlib import Path

root = Path("src")
launcher = root / "launcher"

# Give the standalone APK its own package identity while keeping the source namespace.
gradle = (launcher / "build.gradle.kts").read_text()
gradle = gradle.replace('applicationId = "com.cbkii.ts18launcher"', 'applicationId = "com.ts18.applehome"')
(launcher / "build.gradle.kts").write_text(gradle)

(launcher / "src/main/res/values/strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TS18 Apple Home</string>
    <string name="media_listener_label">TS18 Apple Home 音乐控制</string>
</resources>
""")

(launcher / "src/main/res/values/styles.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="@android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:windowActionModeOverlay">true</item>
        <item name="android:windowBackground">#EEF3F8</item>
        <item name="android:colorAccent">#1677FF</item>
        <item name="android:statusBarColor">#EEF3F8</item>
        <item name="android:navigationBarColor">#EEF3F8</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:windowLightNavigationBar">true</item>
        <item name="android:windowDisablePreview">true</item>
    </style>
</resources>
""")

activity = r'''package com.cbkii.ts18launcher;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextClock;
import android.widget.TextView;

public final class LauncherActivity extends Activity
        implements MediaListenerService.Observer, LocationListener {

    private static final int REQ_LOCATION = 7001;
    private static final String AMAP = "com.autonavi.amapauto";
    private static final String KUWO_CAR = "cn.kuwo.kwmusiccar";
    private static final String KUWO_PHONE = "cn.kuwo.player";

    private FrameLayout root;
    private TextView speedValue;
    private TextView songTitle;
    private TextView songArtist;
    private TextView playPause;
    private TextView mapStatus;
    private MediaListenerService.Snapshot media =
            new MediaListenerService.Snapshot("", "", "", false);
    private LocationManager locationManager;
    private boolean mapWindowAttempted;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(238, 243, 248));
        setContentView(root);
        buildUi();

        MediaListenerService.addObserver(this);
        MediaListenerService.refreshActiveSessions();
        locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
        startLocation();

        // DoFun-style homepage behaviour: keep our dashboard visible while trying to
        // place AMap in the map region as a separate task window on TS18 firmware.
        root.postDelayed(this::tryAmapWindow, 900);
    }

    @Override
    protected void onResume() {
        super.onResume();
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        MediaListenerService.refreshActiveSessions();
    }

    @Override
    protected void onDestroy() {
        MediaListenerService.removeObserver(this);
        if (locationManager != null) {
            try { locationManager.removeUpdates(this); } catch (SecurityException ignored) {}
        }
        super.onDestroy();
    }

    private void buildUi() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(18), dp(10), dp(18), dp(10));
        root.addView(page, match());

        page.addView(buildTopBar(), new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(48)));

        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.HORIZONTAL);
        body.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams bodyLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        page.addView(body, bodyLp);

        LinearLayout left = new LinearLayout(this);
        left.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams leftLp = new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.MATCH_PARENT, 0.34f);
        leftLp.setMargins(0, dp(6), dp(12), dp(6));
        body.addView(left, leftLp);

        View speedCard = buildSpeedCard();
        LinearLayout.LayoutParams speedLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 0.64f);
        speedLp.bottomMargin = dp(12);
        left.addView(speedCard, speedLp);

        View musicCard = buildMusicCard();
        left.addView(musicCard, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 0.36f));

        View map = buildMapArea();
        LinearLayout.LayoutParams mapLp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.MATCH_PARENT, 0.66f);
        mapLp.setMargins(0, dp(6), 0, dp(6));
        body.addView(map, mapLp);

        page.addView(buildDock(), new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(72)));
    }

    private View buildTopBar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);

        bar.addView(topButton("‹", v -> finish()), fixed(46, 42));
        bar.addView(topButton("○", v -> goSystemHome()), fixed(46, 42));
        bar.addView(topButton("≡", v -> openApps()), fixed(46, 42));

        TextView temp = label("30°C   USB", 18, Color.rgb(43, 54, 68), false);
        LinearLayout.LayoutParams mid = new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.MATCH_PARENT, 1f);
        mid.leftMargin = dp(12);
        bar.addView(temp, mid);

        TextView voltage = label("▣ 13.5V   B   GPS   ▥", 17,
                Color.rgb(43, 54, 68), false);
        voltage.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        bar.addView(voltage, new LinearLayout.LayoutParams(dp(260),
                ViewGroup.LayoutParams.MATCH_PARENT));

        TextClock clock = new TextClock(this);
        clock.setFormat24Hour("HH:mm");
        clock.setFormat12Hour("HH:mm");
        clock.setTextSize(21);
        clock.setTypeface(Typeface.DEFAULT_BOLD);
        clock.setTextColor(Color.rgb(36, 45, 58));
        clock.setGravity(Gravity.CENTER);
        bar.addView(clock, fixed(92, 42));
        return bar;
    }

    private View buildSpeedCard() {
        FrameLayout card = card(Color.argb(245, 247, 250, 255), 24);

        CarSceneView scene = new CarSceneView(this);
        card.addView(scene, match());

        LinearLayout text = new LinearLayout(this);
        text.setOrientation(LinearLayout.VERTICAL);
        text.setGravity(Gravity.CENTER_HORIZONTAL);
        FrameLayout.LayoutParams textLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(150));
        textLp.gravity = Gravity.TOP;
        textLp.topMargin = dp(34);
        card.addView(text, textLp);

        speedValue = label("0", 52, Color.rgb(26, 36, 50), true);
        speedValue.setGravity(Gravity.CENTER);
        text.addView(speedValue, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(70)));

        TextView unit = label("公里/时", 23, Color.rgb(63, 82, 111), false);
        unit.setGravity(Gravity.CENTER);
        text.addView(unit, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(42)));

        TextView title = label("车辆状态", 15, Color.rgb(105, 121, 143), false);
        FrameLayout.LayoutParams titleLp = new FrameLayout.LayoutParams(
                dp(120), dp(34));
        titleLp.gravity = Gravity.TOP | Gravity.LEFT;
        titleLp.leftMargin = dp(18);
        titleLp.topMargin = dp(14);
        card.addView(title, titleLp);
        return card;
    }

    private View buildMusicCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(round(Color.argb(246,255,255,255), 24));
        card.setOnClickListener(v -> openMusic());

        TextView cover = label("K", 34, Color.WHITE, true);
        cover.setGravity(Gravity.CENTER);
        GradientDrawable cg = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(255, 185, 40), Color.rgb(255, 117, 54)});
        cg.setCornerRadius(dp(18));
        cover.setBackground(cg);
        card.addView(cover, fixed(92, 92));

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.VERTICAL);
        info.setPadding(dp(14), 0, 0, 0);
        card.addView(info, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));

        TextView app = label("酷我音乐", 15, Color.rgb(78, 91, 110), true);
        info.addView(app, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(28)));

        songTitle = label("打开酷我开始播放", 22, Color.rgb(29, 40, 55), true);
        songTitle.setSingleLine(true);
        info.addView(songTitle, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(36)));

        songArtist = label("允许“通知使用权”后可控制音乐", 14,
                Color.rgb(113, 127, 148), false);
        songArtist.setSingleLine(true);
        info.addView(songArtist, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(28)));

        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        controls.setGravity(Gravity.CENTER_VERTICAL);
        info.addView(controls, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        controls.addView(mediaButton("◀", v ->
                MediaListenerService.sendGeneric(
                        MediaListenerService.Command.PREVIOUS)), fixed(58, 48));
        playPause = mediaButton("▶", v ->
                MediaListenerService.sendGeneric(
                        MediaListenerService.Command.PLAY_PAUSE));
        controls.addView(playPause, fixed(58, 48));
        controls.addView(mediaButton("▶|", v ->
                MediaListenerService.sendGeneric(
                        MediaListenerService.Command.NEXT)), fixed(58, 48));
        return card;
    }

    private View buildMapArea() {
        FrameLayout card = card(Color.WHITE, 24);
        MapPreviewView preview = new MapPreviewView(this);
        card.addView(preview, match());

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.VERTICAL);
        top.setPadding(dp(18), dp(18), dp(18), 0);
        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(220));
        topLp.gravity = Gravity.TOP;
        card.addView(top, topLp);

        TextView search = label("⌕   搜索目的地                                    🎙",
                20, Color.rgb(30, 43, 61), true);
        search.setGravity(Gravity.CENTER_VERTICAL);
        search.setPadding(dp(20), 0, dp(20), 0);
        search.setBackground(round(Color.argb(238, 250, 252, 255), 20));
        search.setOnClickListener(v -> openAmapFull());
        top.addView(search, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(58)));

        LinearLayout quick = new LinearLayout(this);
        quick.setOrientation(LinearLayout.HORIZONTAL);
        quick.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams qlp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(56));
        qlp.topMargin = dp(8);
        top.addView(quick, qlp);
        String[] items = {"⛽ 加油", "🚗 洗车", "🍴 美食", "▦ 更多"};
        for (String item : items) {
            TextView q = label(item, 15, Color.rgb(38, 91, 161), true);
            q.setGravity(Gravity.CENTER);
            quick.addView(q, new LinearLayout.LayoutParams(
                    0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));
        }

        LinearLayout destinations = new LinearLayout(this);
        destinations.setOrientation(LinearLayout.HORIZONTAL);
        destinations.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams dlp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(72));
        dlp.topMargin = dp(8);
        top.addView(destinations, dlp);

        destinations.addView(shortcut("⌂", "回家", "已在附近", v -> openAmapFull()),
                new LinearLayout.LayoutParams(0,
                        ViewGroup.LayoutParams.MATCH_PARENT, 1f));
        View spacer = new View(this);
        destinations.addView(spacer, new LinearLayout.LayoutParams(dp(10), 1));
        destinations.addView(shortcut("▣", "去公司", "8.0公里", v -> openAmapFull()),
                new LinearLayout.LayoutParams(0,
                        ViewGroup.LayoutParams.MATCH_PARENT, 1f));

        mapStatus = label("高德地图 · 点击打开", 15,
                Color.rgb(34, 105, 199), true);
        mapStatus.setGravity(Gravity.CENTER);
        mapStatus.setBackground(round(Color.argb(230,255,255,255), 18));
        mapStatus.setOnClickListener(v -> tryAmapWindow());
        FrameLayout.LayoutParams statusLp = new FrameLayout.LayoutParams(dp(220), dp(46));
        statusLp.gravity = Gravity.BOTTOM | Gravity.RIGHT;
        statusLp.rightMargin = dp(18);
        statusLp.bottomMargin = dp(18);
        card.addView(mapStatus, statusLp);

        TextView marker = label("▲", 34, Color.rgb(18, 105, 235), true);
        marker.setGravity(Gravity.CENTER);
        marker.setBackground(round(Color.argb(235,255,255,255), 30));
        FrameLayout.LayoutParams mlp = new FrameLayout.LayoutParams(dp(62), dp(62));
        mlp.gravity = Gravity.BOTTOM | Gravity.RIGHT;
        mlp.rightMargin = dp(252);
        mlp.bottomMargin = dp(16);
        card.addView(marker, mlp);

        return card;
    }

    private View buildDock() {
        LinearLayout dock = new LinearLayout(this);
        dock.setOrientation(LinearLayout.HORIZONTAL);
        dock.setGravity(Gravity.CENTER);
        dock.setPadding(dp(8), dp(6), dp(8), dp(6));
        dock.setBackground(round(Color.argb(244, 247, 250, 255), 24));

        dock.addView(dockItem("➤", "导航", true, v -> tryAmapWindow()), weighted());
        dock.addView(dockItem("♫", "音乐", false, v -> openMusic()), weighted());
        dock.addView(dockItem("▦", "应用", false, v -> openApps()), weighted());
        dock.addView(dockItem("●", "记录仪", false, v -> openAny(
                "com.tw.dvr", "com.android.camera2", "com.android.camera")), weighted());
        dock.addView(dockItem("⚙", "设置", false, v -> startActivity(
                new Intent(Settings.ACTION_SETTINGS))), weighted());
        return dock;
    }

    private View shortcut(String icon, String title, String sub, View.OnClickListener click) {
        LinearLayout v = new LinearLayout(this);
        v.setOrientation(LinearLayout.HORIZONTAL);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(16), 0, dp(14), 0);
        v.setBackground(round(Color.argb(235, 247, 250, 255), 18));
        v.setOnClickListener(click);

        TextView i = label(icon, 26, Color.rgb(20, 112, 235), true);
        i.setGravity(Gravity.CENTER);
        v.addView(i, fixed(50, 50));

        LinearLayout txt = new LinearLayout(this);
        txt.setOrientation(LinearLayout.VERTICAL);
        txt.setGravity(Gravity.CENTER_VERTICAL);
        v.addView(txt, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));
        TextView t = label(title, 18, Color.rgb(30, 42, 58), true);
        TextView s = label(sub, 13, Color.rgb(104, 120, 143), false);
        txt.addView(t, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(30)));
        txt.addView(s, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(24)));
        return v;
    }

    private TextView dockItem(String icon, String title, boolean selected,
                              View.OnClickListener click) {
        TextView v = label(icon + "\n" + title, 15,
                selected ? Color.rgb(20, 105, 235) : Color.rgb(62, 83, 113), true);
        v.setGravity(Gravity.CENTER);
        v.setOnClickListener(click);
        if (selected) v.setBackground(round(Color.argb(105, 202, 225, 255), 18));
        return v;
    }

    private TextView topButton(String text, View.OnClickListener click) {
        TextView v = label(text, 31, Color.rgb(38, 50, 66), false);
        v.setGravity(Gravity.CENTER);
        v.setOnClickListener(click);
        return v;
    }

    private TextView mediaButton(String text, View.OnClickListener click) {
        TextView v = label(text, 24, Color.rgb(54, 74, 103), true);
        v.setGravity(Gravity.CENTER);
        v.setOnClickListener(click);
        return v;
    }

    private void startLocation() {
        if (locationManager == null) return;
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_LOCATION);
            return;
        }
        try {
            locationManager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER, 1000L, 0f, this);
        } catch (RuntimeException ignored) {}
    }

    @Override
    public void onLocationChanged(Location location) {
        if (location == null || speedValue == null) return;
        float kmh = Math.max(0f, location.getSpeed() * 3.6f);
        speedValue.setText(String.valueOf(Math.round(kmh)));
    }

    @Override public void onProviderEnabled(String provider) {}
    @Override public void onProviderDisabled(String provider) {}
    @Override public void onStatusChanged(String provider, int status, Bundle extras) {}

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                           int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_LOCATION) startLocation();
    }

    @Override
    public void onMediaStateChanged(MediaListenerService.Snapshot genericMedia,
                                    MediaListenerService.Snapshot radio) {
        media = genericMedia == null
                ? new MediaListenerService.Snapshot("", "", "", false) : genericMedia;
        runOnUiThread(() -> {
            if (!MediaListenerService.hasNotificationAccess(this)) {
                songTitle.setText("点这里授权音乐控制");
                songArtist.setText("授权后显示酷我歌曲和控制按键");
                playPause.setText("▶");
                return;
            }
            if (!media.title.isEmpty()) songTitle.setText(media.title);
            else songTitle.setText("酷我音乐");
            if (!media.artist.isEmpty()) songArtist.setText(media.artist);
            else if (!media.packageName.isEmpty()) songArtist.setText(media.packageName);
            else songArtist.setText("打开酷我开始播放");
            playPause.setText(media.playing ? "Ⅱ" : "▶");
        });
    }

    private void openMusic() {
        if (!MediaListenerService.hasNotificationAccess(this)) {
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
            return;
        }
        if (!openPackage(KUWO_CAR)) openPackage(KUWO_PHONE);
    }

    private void tryAmapWindow() {
        if (!isInstalled(AMAP)) {
            mapStatus.setText("未安装高德车机版");
            return;
        }
        mapStatus.setText("正在尝试主页窗口…");
        new Thread(() -> {
            String cmd =
                    "COMP=$(cmd package resolve-activity --brief "
                    + "-a android.intent.action.MAIN "
                    + "-c android.intent.category.LAUNCHER " + AMAP
                    + " | tail -n 1); "
                    + "test -n \\\"$COMP\\\" && "
                    + "am start --activity-new-task --windowingMode 5 "
                    + "--bounds 430,245,1220,650 -n \\\"$COMP\\\"";
            RootShell.Result result = RootShell.run(cmd, 5);
            runOnUiThread(() -> {
                mapWindowAttempted = true;
                if (result.success()) {
                    mapStatus.setText("高德窗口模式 · 点击重开");
                } else {
                    mapStatus.setText("此固件未开放窗口 · 点击全屏");
                    mapStatus.setOnClickListener(v -> openAmapFull());
                }
            });
        }, "amap-window").start();
    }

    private void openAmapFull() {
        if (!openPackage(AMAP)) {
            mapStatus.setText("请先安装高德车机版");
        }
    }

    private void openApps() {
        try {
            startActivity(new Intent(this, AppDrawerActivity.class));
        } catch (RuntimeException ignored) {}
    }

    private void goSystemHome() {
        Intent i = new Intent(Intent.ACTION_MAIN);
        i.addCategory(Intent.CATEGORY_HOME);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try { startActivity(i); } catch (RuntimeException ignored) {}
    }

    private boolean openPackage(String pkg) {
        if (pkg == null || pkg.isEmpty()) return false;
        try {
            Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
            if (i == null) return false;
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
            return true;
        } catch (RuntimeException e) {
            return false;
        }
    }

    private void openAny(String... pkgs) {
        for (String p : pkgs) if (openPackage(p)) return;
    }

    private boolean isInstalled(String pkg) {
        try {
            getPackageManager().getPackageInfo(pkg, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    private FrameLayout card(int color, int radius) {
        FrameLayout v = new FrameLayout(this);
        v.setBackground(round(color, radius));
        v.setClipToOutline(false);
        v.setElevation(dp(3));
        return v;
    }

    private GradientDrawable round(int color, int radiusDp) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        g.setStroke(dp(1), Color.argb(35, 60, 80, 100));
        return g;
    }

    private TextView label(String text, float size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(size);
        v.setTextColor(color);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL);
        return v;
    }

    private FrameLayout.LayoutParams match() {
        return new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
    }

    private LinearLayout.LayoutParams fixed(int w, int h) {
        return new LinearLayout.LayoutParams(dp(w), dp(h));
    }

    private LinearLayout.LayoutParams weighted() {
        return new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.MATCH_PARENT, 1f);
    }

    private int dp(float v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private final class CarSceneView extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        CarSceneView(Context c) { super(c); }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            int w = getWidth(), h = getHeight();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(224, 239, 250));
            c.drawRoundRect(new RectF(0,0,w,h), dp(24), dp(24), p);

            p.setColor(Color.rgb(206, 226, 242));
            c.drawOval(new RectF(-w*.05f,h*.45f,w*1.05f,h*1.08f),p);

            p.setColor(Color.argb(120,255,255,255));
            Path l = new Path();
            l.moveTo(w*.18f,h*.98f); l.lineTo(w*.43f,h*.62f);
            l.lineTo(w*.46f,h*.62f); l.lineTo(w*.35f,h*.98f); l.close();
            c.drawPath(l,p);
            Path r = new Path();
            r.moveTo(w*.82f,h*.98f); r.lineTo(w*.57f,h*.62f);
            r.lineTo(w*.54f,h*.62f); r.lineTo(w*.65f,h*.98f); r.close();
            c.drawPath(r,p);

            float cx=w*.5f, cy=h*.73f;
            p.setColor(Color.rgb(223,229,236));
            c.drawRoundRect(new RectF(cx-w*.19f,cy-h*.08f,cx+w*.19f,cy+h*.13f),
                    dp(20),dp(20),p);
            p.setColor(Color.rgb(70,88,111));
            c.drawRoundRect(new RectF(cx-w*.12f,cy-h*.05f,cx+w*.12f,cy+h*.025f),
                    dp(10),dp(10),p);
            p.setColor(Color.rgb(30,39,52));
            c.drawRoundRect(new RectF(cx-w*.16f,cy+h*.055f,cx+w*.16f,cy+h*.12f),
                    dp(8),dp(8),p);
            p.setColor(Color.rgb(240,57,75));
            c.drawRect(cx-w*.145f,cy+h*.066f,cx+w*.145f,cy+h*.078f,p);
        }
    }

    private final class MapPreviewView extends View {
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        MapPreviewView(Context c) { super(c); }
        @Override protected void onDraw(Canvas c) {
            int w=getWidth(), h=getHeight();
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(232, 239, 238));
            c.drawRoundRect(new RectF(0,0,w,h),dp(24),dp(24),p);

            p.setStrokeCap(Paint.Cap.ROUND);
            for (int i=0;i<8;i++) {
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(dp(5));
                p.setColor(i%2==0 ? Color.rgb(255,255,255) : Color.rgb(210,218,220));
                float y = h*(.30f + i*.075f);
                c.drawLine(w*.05f,y,w*.97f,y+(i%3-1)*dp(42),p);
            }
            for (int i=0;i<6;i++) {
                p.setStrokeWidth(dp(4));
                p.setColor(Color.rgb(255,255,255));
                float x=w*(.42f+i*.095f);
                c.drawLine(x,h*.16f,x-dp(90),h*.95f,p);
            }

            p.setStrokeWidth(dp(8));
            p.setColor(Color.rgb(65, 196, 106));
            c.drawLine(w*.46f,h*.66f,w*.70f,h*.59f,p);
            p.setColor(Color.rgb(248, 190, 52));
            c.drawLine(w*.70f,h*.59f,w*.84f,h*.50f,p);
            p.setColor(Color.rgb(238, 81, 74));
            c.drawLine(w*.84f,h*.50f,w*.96f,h*.43f,p);

            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(28,111,235));
            c.drawCircle(w*.73f,h*.70f,dp(11),p);
            p.setColor(Color.WHITE);
            c.drawCircle(w*.73f,h*.70f,dp(4),p);
        }
    }
}
'''
(launcher / "src/main/java/com/cbkii/ts18launcher/LauncherActivity.java").write_text(activity)
print("Patched standalone TS18 Apple-style home app.")
