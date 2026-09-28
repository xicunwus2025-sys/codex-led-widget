from pathlib import Path

root = Path("src")
launcher = root / "launcher"

gradle = (launcher / "build.gradle.kts").read_text()
gradle = gradle.replace('applicationId = "com.cbkii.ts18launcher"', 'applicationId = "com.ts18.dofunthemecapture"')
(launcher / "build.gradle.kts").write_text(gradle)

(launcher / "src/main/res/values/strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">兜风在线主题捕获</string>
</resources>
""")

(launcher / "src/main/res/values/styles.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="@android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:windowBackground">#F4F7FB</item>
        <item name="android:colorAccent">#1677FF</item>
        <item name="android:statusBarColor">#F4F7FB</item>
        <item name="android:navigationBarColor">#F4F7FB</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:windowLightNavigationBar">true</item>
    </style>
</resources>
""")

(launcher / "src/main/AndroidManifest.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:allowBackup="false"
        android:hardwareAccelerated="true"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:requestLegacyExternalStorage="true"
        android:supportsRtl="false"
        android:theme="@style/AppTheme">
        <activity
            android:name=".LauncherActivity"
            android:exported="true"
            android:screenOrientation="landscape">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

activity = r'''package com.cbkii.ts18launcher;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public final class LauncherActivity extends Activity {
    private static final int REQ_STORAGE = 9001;
    private static final String DOFUN = "com.dofun.variety";
    private static final String ONLINE_URI = "launcher://variety/online/theme";
    private static final String PREFS = "capture";
    private TextView status;
    private TextView results;

    static final class Sig {
        final long size;
        final long modified;
        Sig(long size, long modified) { this.size = size; this.modified = modified; }
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        ensureStoragePermission();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(244,247,251));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(16), dp(24), dp(18));
        scroll.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);

        TextView title = text("兜风在线主题捕获", 28, Color.rgb(28,39,55), true);
        root.addView(title, lp(dp(48)));

        TextView desc = text(
                "用途：只捕获你在兜风里正常下载的免费/试用主题文件，不修改兜风、不绕过购买授权。",
                15, Color.rgb(88,104,126), false);
        LinearLayout.LayoutParams dlp = lp(dp(52));
        dlp.bottomMargin = dp(10);
        root.addView(desc, dlp);

        status = text("准备中…", 14, Color.rgb(59,75,98), false);
        status.setPadding(dp(14), dp(10), dp(14), dp(10));
        status.setBackground(round(Color.WHITE, 14));
        LinearLayout.LayoutParams slp = lp(dp(56));
        slp.bottomMargin = dp(12);
        root.addView(status, slp);

        TextView one = button("1  记录下载前状态");
        one.setOnClickListener(v -> snapshotBefore());
        root.addView(one, buttonLp());

        TextView two = button("2  打开兜风在线主题");
        two.setOnClickListener(v -> openOnlineThemes());
        root.addView(two, buttonLp());

        TextView three = button("3  下载后扫描并复制新增主题文件");
        three.setOnClickListener(v -> scanAfter());
        root.addView(three, buttonLp());

        TextView four = button("4  仅扫描最近 30 分钟文件");
        four.setOnClickListener(v -> scanRecent());
        root.addView(four, buttonLp());

        results = text(
                "操作顺序：1 → 2 → 在兜风里选一款官方标记“免费/试用”的主题下载完成 → 返回本工具 → 3。",
                14, Color.rgb(44,57,76), false);
        results.setPadding(dp(14), dp(12), dp(14), dp(12));
        results.setBackground(round(Color.rgb(235,242,252), 14));
        root.addView(results, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
    }

    private void ensureStoragePermission() {
        if (checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {
                    Manifest.permission.READ_EXTERNAL_STORAGE,
                    Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
        } else {
            status.setText("存储权限已就绪。先点“1 记录下载前状态”。");
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                           int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_STORAGE) {
            boolean ok = true;
            for (int g : grantResults) if (g != PackageManager.PERMISSION_GRANTED) ok = false;
            status.setText(ok ? "存储权限已授权。" : "没有存储权限，无法扫描主题文件。");
        }
    }

    private void snapshotBefore() {
        runAsync("正在记录下载前状态…", () -> {
            Map<String,Sig> map = scanStorage(false);
            saveSnapshot(map);
            runOnUiThread(() -> {
                status.setText("已记录 " + map.size() + " 个候选文件。现在点 2 打开在线主题。");
                results.setText("基线已保存。接下来只下载官方标记为免费/试用的主题。");
            });
        });
    }

    private void openOnlineThemes() {
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(ONLINE_URI));
        i.setPackage(DOFUN);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
            status.setText("已打开兜风在线主题。下载完成后返回本工具点 3。");
        } catch (Exception e) {
            status.setText("在线主题入口打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void scanAfter() {
        runAsync("正在比较下载前后文件…", () -> {
            Map<String,Sig> before = loadSnapshot();
            Map<String,Sig> after = scanStorage(false);
            List<File> changed = new ArrayList<>();
            for (Map.Entry<String,Sig> e : after.entrySet()) {
                Sig old = before.get(e.getKey());
                Sig now = e.getValue();
                if (old == null || old.size != now.size || old.modified != now.modified) {
                    changed.add(new File(e.getKey()));
                }
            }
            Collections.sort(changed, (a,b) -> Long.compare(b.lastModified(), a.lastModified()));
            File out = new File(Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS), "DoFunThemeCapture");
            if (!out.exists()) out.mkdirs();

            StringBuilder report = new StringBuilder();
            report.append("发现新增/变化候选：").append(changed.size()).append("\\n");
            int copied = 0;
            for (File f : changed) {
                report.append("\\n").append(f.getAbsolutePath())
                      .append("\\n  ").append(f.length()).append(" bytes  ")
                      .append(formatTime(f.lastModified()));
                if (f.isFile() && f.length() > 0 && f.length() <= 120L * 1024 * 1024) {
                    File dst = new File(out, safeName(f));
                    if (copy(f, dst)) {
                        copied++;
                        report.append("\\n  -> ").append(dst.getAbsolutePath());
                    }
                }
                if (report.length() > 12000) break;
            }
            final String text = report.toString();
            final int cc = copied;
            runOnUiThread(() -> {
                status.setText("扫描完成，已复制 " + cc + " 个候选文件到 Download/DoFunThemeCapture/");
                results.setText(text);
            });
        });
    }

    private void scanRecent() {
        runAsync("正在扫描最近文件…", () -> {
            long cutoff = System.currentTimeMillis() - 30L * 60L * 1000L;
            Map<String,Sig> all = scanStorage(true);
            List<File> files = new ArrayList<>();
            for (String p : all.keySet()) {
                File f = new File(p);
                if (f.lastModified() >= cutoff) files.add(f);
            }
            Collections.sort(files, (a,b) -> Long.compare(b.lastModified(), a.lastModified()));
            StringBuilder sb = new StringBuilder();
            sb.append("最近 30 分钟候选文件：").append(files.size()).append("\\n");
            for (File f : files) {
                sb.append("\\n").append(f.getAbsolutePath())
                  .append("\\n  ").append(f.length()).append(" bytes  ")
                  .append(formatTime(f.lastModified()));
                if (sb.length() > 12000) break;
            }
            final String text = sb.toString();
            runOnUiThread(() -> {
                status.setText("最近文件扫描完成。");
                results.setText(text);
            });
        });
    }

    private Map<String,Sig> scanStorage(boolean recentMode) {
        Map<String,Sig> out = new HashMap<>();
        File sd = Environment.getExternalStorageDirectory();
        if (sd == null) return out;

        ArrayDeque<File> q = new ArrayDeque<>();
        q.add(sd);
        int visited = 0;
        final int MAX_VISITED = 40000;

        while (!q.isEmpty() && visited < MAX_VISITED) {
            File f = q.removeFirst();
            visited++;
            if (f == null || !f.exists()) continue;
            if (f.isDirectory()) {
                String path = f.getAbsolutePath().toLowerCase(Locale.US);
                if (path.contains("/android/obb/")) continue;
                File[] kids;
                try { kids = f.listFiles(); } catch (Exception e) { kids = null; }
                if (kids == null) continue;
                for (File k : kids) q.addLast(k);
            } else if (isCandidate(f, recentMode)) {
                out.put(f.getAbsolutePath(), new Sig(f.length(), f.lastModified()));
            }
        }
        return out;
    }

    private boolean isCandidate(File f, boolean recentMode) {
        String p = f.getAbsolutePath().toLowerCase(Locale.US);
        String n = f.getName().toLowerCase(Locale.US);
        boolean ext = n.endsWith(".apk") || n.endsWith(".jar") || n.endsWith(".zip")
                || n.endsWith(".json") || n.endsWith(".dat") || n.endsWith(".bin")
                || n.endsWith(".theme") || n.endsWith(".tmp") || n.endsWith(".download");
        boolean pathHint = p.contains("dofun") || p.contains("variety")
                || p.contains("/theme") || p.contains("plugin") || p.contains("cardoor");
        if (recentMode) {
            return (ext || pathHint) && f.length() >= 0;
        }
        return ext || pathHint;
    }

    private void saveSnapshot(Map<String,Sig> map) {
        try {
            JSONArray a = new JSONArray();
            for (Map.Entry<String,Sig> e : map.entrySet()) {
                JSONObject o = new JSONObject();
                o.put("p", e.getKey());
                o.put("s", e.getValue().size);
                o.put("m", e.getValue().modified);
                a.put(o);
            }
            getSharedPreferences(PREFS, MODE_PRIVATE)
                    .edit().putString("snapshot", a.toString()).apply();
        } catch (Exception ignored) {}
    }

    private Map<String,Sig> loadSnapshot() {
        Map<String,Sig> out = new HashMap<>();
        String raw = getSharedPreferences(PREFS, MODE_PRIVATE).getString("snapshot", "[]");
        try {
            JSONArray a = new JSONArray(raw);
            for (int i=0;i<a.length();i++) {
                JSONObject o = a.getJSONObject(i);
                out.put(o.getString("p"), new Sig(o.getLong("s"), o.getLong("m")));
            }
        } catch (Exception ignored) {}
        return out;
    }

    private boolean copy(File src, File dst) {
        try (FileInputStream in = new FileInputStream(src);
             FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf,0,n);
            out.flush();
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private String safeName(File f) {
        String base = f.getName().replaceAll("[^A-Za-z0-9._-]", "_");
        if (base.isEmpty()) base = "capture.bin";
        String parent = f.getParent() == null ? "" : f.getParent();
        String tag = Integer.toHexString(parent.hashCode());
        return tag + "_" + base;
    }

    private String formatTime(long t) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                .format(new Date(t));
    }

    private void runAsync(String msg, Runnable r) {
        status.setText(msg);
        new Thread(r, "dofun-theme-capture").start();
    }

    private TextView button(String s) {
        TextView v = text(s, 17, Color.rgb(27,66,126), true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(18),0,dp(18),0);
        v.setBackground(round(Color.WHITE,15));
        return v;
    }

    private LinearLayout.LayoutParams buttonLp() {
        LinearLayout.LayoutParams p = lp(dp(56));
        p.bottomMargin = dp(9);
        return p;
    }

    private LinearLayout.LayoutParams lp(int h) {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, h);
    }

    private TextView text(String s, float size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(s);
        v.setTextSize(size);
        v.setTextColor(color);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL);
        return v;
    }

    private GradientDrawable round(int color, int radiusDp) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        g.setStroke(dp(1), Color.argb(28,60,85,115));
        return g;
    }

    private int dp(float v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
'''
(launcher / "src/main/java/com/cbkii/ts18launcher/LauncherActivity.java").write_text(activity)
print("Patched DoFun online theme capture app.")
