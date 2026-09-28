from pathlib import Path

root = Path("src")
launcher = root / "launcher"

gradle = (launcher / "build.gradle.kts").read_text()
gradle = gradle.replace('applicationId = "com.cbkii.ts18launcher"', 'applicationId = "com.ts18.dofunmemberrepair"')
(launcher / "build.gradle.kts").write_text(gradle)

(launcher / "src/main/res/values/strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">兜风会员修复助手</string>
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
    <application
        android:allowBackup="false"
        android:hardwareAccelerated="true"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
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

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class LauncherActivity extends Activity {
    private static final String PKG = "com.dofun.variety";
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
    }

    private void buildUi() {
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.rgb(244,247,251));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(18), dp(24), dp(18));
        sv.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(sv);

        TextView title = text("兜风会员修复助手", 28, Color.rgb(28,39,55), true);
        root.addView(title, lp(dp(48)));

        TextView desc = text(
                "用于“账号已有真实会员，但兜风显示 No VIP / 未开通 / 已购主题无法恢复”的兼容修复。"
                + "不修改会员状态，只让原版兜风重新刷新登录、Token 和在线主题状态。",
                15, Color.rgb(84,101,124), false);
        LinearLayout.LayoutParams dlp = lp(dp(66));
        dlp.bottomMargin = dp(10);
        root.addView(desc, dlp);

        status = text(appInfo(), 14, Color.rgb(57,74,97), false);
        status.setPadding(dp(14), dp(10), dp(14), dp(10));
        status.setBackground(round(Color.WHITE, 14));
        LinearLayout.LayoutParams slp = lp(dp(58));
        slp.bottomMargin = dp(12);
        root.addView(status, slp);

        add(root, "1  打开兜风官方登录", () ->
                openExplicit("cn.cardoor.user.view.LoginActivity"));

        add(root, "2  打开账号/我的页面", () ->
                openExplicit("com.dofun.variety.mine.MineActivity"));

        add(root, "3  打开在线主题并刷新授权", () ->
                openDeepLink("launcher://variety/online/theme"));

        add(root, "4  打开主题详情入口", () ->
                openDeepLink("launcher://variety/theme/category/details"));

        add(root, "5  打开兜风应用设置（清缓存）", this::openAppSettings);

        add(root, "6  检查系统日期和时间", this::openDateSettings);

        add(root, "7  正常启动兜风", this::openPackage);

        TextView note = text(
                "建议顺序：先 1 重新登录 → 2 确认账号 → 6 确认时间正确 → 3 打开在线主题。"
                + "如果仍显示“Token invalid / No VIP / No payment order found”，把提示拍给我。",
                15, Color.rgb(48,62,82), false);
        note.setPadding(dp(14), dp(12), dp(14), dp(12));
        note.setBackground(round(Color.rgb(233,241,252), 14));
        root.addView(note, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
    }

    private void add(LinearLayout root, String label, Runnable action) {
        TextView b = button(label);
        b.setOnClickListener(v -> action.run());
        root.addView(b, buttonLp());
    }

    private void openExplicit(String cls) {
        Intent i = new Intent();
        i.setClassName(PKG, cls);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
            status.setText("已打开：" + cls);
        } catch (SecurityException e) {
            status.setText("该页面存在，但原版兜风不允许第三方直接启动：" + cls);
        } catch (ActivityNotFoundException e) {
            status.setText("未找到页面：" + cls);
        } catch (RuntimeException e) {
            status.setText("打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openDeepLink(String uri) {
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(uri));
        i.setPackage(PKG);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
            status.setText("已请求原版兜风刷新：" + uri);
        } catch (Exception e) {
            status.setText("入口打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openAppSettings() {
        try {
            Intent i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + PKG));
            startActivity(i);
            status.setText("已打开兜风应用设置。只清“缓存”，不要清数据，除非你愿意重新登录。");
        } catch (Exception e) {
            status.setText("应用设置打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openDateSettings() {
        try {
            startActivity(new Intent(Settings.ACTION_DATE_SETTINGS));
            status.setText("请确认自动日期/时间和时区正确。错误时间会导致 Token/有效期校验异常。");
        } catch (Exception e) {
            status.setText("日期设置打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openPackage() {
        Intent i = getPackageManager().getLaunchIntentForPackage(PKG);
        if (i == null) {
            status.setText("未检测到原版兜风：" + PKG);
            return;
        }
        try {
            startActivity(i);
        } catch (RuntimeException e) {
            status.setText("兜风启动失败：" + e.getClass().getSimpleName());
        }
    }

    private String appInfo() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(PKG, 0);
            return "检测到原版兜风：" + p.versionName + "    package=" + PKG;
        } catch (Exception e) {
            return "未检测到原版兜风：" + PKG;
        }
    }

    private TextView button(String s) {
        TextView v = text(s, 17, Color.rgb(27,66,126), true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(18), 0, dp(18), 0);
        v.setBackground(round(Color.WHITE, 15));
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
print("Patched DoFun member repair helper.")
