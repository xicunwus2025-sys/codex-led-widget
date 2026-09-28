from pathlib import Path

root = Path("src")
launcher = root / "launcher"

gradle = (launcher / "build.gradle.kts").read_text()
gradle = gradle.replace('applicationId = "com.cbkii.ts18launcher"', 'applicationId = "com.ts18.dofunentry"')
(launcher / "build.gradle.kts").write_text(gradle)

(launcher / "src/main/res/values/strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">兜风隐藏入口测试</string>
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
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class LauncherActivity extends Activity {
    private static final String DOFUN = "com.dofun.variety";
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(244, 247, 251));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(28), dp(22), dp(28), dp(22));
        scroll.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);

        TextView title = text("兜风隐藏入口测试", 30, Color.rgb(28, 39, 55), true);
        root.addView(title, lpMatch(dp(52)));

        TextView sub = text("只调用兜风自己公开/可解析的页面，不修改主题、不改数据。", 17,
                Color.rgb(93, 108, 129), false);
        LinearLayout.LayoutParams subLp = lpMatch(dp(42));
        subLp.bottomMargin = dp(14);
        root.addView(sub, subLp);

        status = text(dofunInfo(), 15, Color.rgb(66, 82, 105), false);
        status.setPadding(dp(16), dp(12), dp(16), dp(12));
        status.setBackground(round(Color.WHITE, 16));
        LinearLayout.LayoutParams stLp = lpMatch(dp(62));
        stLp.bottomMargin = dp(18);
        root.addView(status, stLp);

        addButton(root, "1  打开主题设计器",
                "launcher://variety/theme/designer/details");
        addButton(root, "2  打开主题一级分类",
                "launcher://variety/theme/category/one");
        addButton(root, "3  打开主题二级分类",
                "launcher://variety/theme/category/two");
        addButton(root, "4  打开在线主题",
                "launcher://variety/online/theme");
        addButton(root, "5  打开主题搜索",
                "launcher://variety/theme/search");
        addButton(root, "6  打开主题详情",
                "launcher://variety/theme/category/details");

        TextView direct = button("7  直接尝试 DesignerActivity");
        direct.setOnClickListener(v -> openExplicit(
                "com.dofun.variety.designer.DesignerActivity"));
        root.addView(direct, buttonLp());

        TextView importer = button("8  直接尝试 CustomImportActivity");
        importer.setOnClickListener(v -> openExplicit(
                "com.dofun.variety.img_picker.CustomImportActivity"));
        root.addView(importer, buttonLp());

        TextView home = button("9  正常打开兜风");
        home.setOnClickListener(v -> openPackage());
        root.addView(home, buttonLp());

        TextView note = text(
                "测试重点：先点 1。如果进入了隐藏的主题设计页面，直接拍照给我。"
                + " 如果提示“未找到可打开页面”，再依次点 2～8。",
                16, Color.rgb(54, 68, 88), false);
        note.setPadding(dp(16), dp(14), dp(16), dp(14));
        note.setBackground(round(Color.rgb(232, 241, 255), 16));
        LinearLayout.LayoutParams noteLp = lpMatch(dp(86));
        noteLp.topMargin = dp(8);
        root.addView(note, noteLp);
    }

    private void addButton(LinearLayout root, String label, String uri) {
        TextView b = button(label);
        b.setOnClickListener(v -> openUri(uri));
        root.addView(b, buttonLp());
    }

    private void openUri(String uri) {
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(uri));
        i.setPackage(DOFUN);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
            setStatus("已发送：" + uri);
        } catch (ActivityNotFoundException e) {
            setStatus("未找到可处理该入口：" + uri);
        } catch (SecurityException e) {
            setStatus("入口存在但被权限阻止：" + uri);
        } catch (RuntimeException e) {
            setStatus("打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openExplicit(String className) {
        Intent i = new Intent();
        i.setClassName(DOFUN, className);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
            setStatus("已尝试：" + className);
        } catch (ActivityNotFoundException e) {
            setStatus("Activity 不存在或名称不同：" + className);
        } catch (SecurityException e) {
            setStatus("Activity 存在，但不允许第三方直接启动：" + className);
        } catch (RuntimeException e) {
            setStatus("打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openPackage() {
        Intent i = getPackageManager().getLaunchIntentForPackage(DOFUN);
        if (i == null) {
            setStatus("未检测到 com.dofun.variety");
            return;
        }
        try {
            startActivity(i);
        } catch (RuntimeException e) {
            setStatus("兜风启动失败：" + e.getClass().getSimpleName());
        }
    }

    private String dofunInfo() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(DOFUN, 0);
            return "检测到兜风：" + p.versionName + "    package=" + DOFUN;
        } catch (Exception e) {
            return "未检测到兜风包：" + DOFUN;
        }
    }

    private void setStatus(String s) {
        if (status != null) status.setText(s);
    }

    private TextView button(String s) {
        TextView v = text(s, 18, Color.rgb(27, 66, 126), true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(20), 0, dp(20), 0);
        v.setBackground(round(Color.WHITE, 16));
        return v;
    }

    private LinearLayout.LayoutParams buttonLp() {
        LinearLayout.LayoutParams lp = lpMatch(dp(58));
        lp.bottomMargin = dp(10);
        return lp;
    }

    private LinearLayout.LayoutParams lpMatch(int h) {
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
        g.setStroke(dp(1), Color.argb(28, 60, 85, 115));
        return g;
    }

    private int dp(float v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
'''
(launcher / "src/main/java/com/cbkii/ts18launcher/LauncherActivity.java").write_text(activity)

print("Patched DoFun hidden-entry tester.")
