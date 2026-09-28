from pathlib import Path

# Apply v1 base changes first.
exec(Path("build-tools/dofun_entry_tester_patch.py").read_text())

launcher = Path("src/launcher")
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
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class LauncherActivity extends Activity {
    private static final String DOFUN = "com.dofun.variety";
    private static final String DESIGNER = "com.dofun.variety.designer.DesignerActivity";
    private static final String BASE = "launcher://variety/theme/designer/details";
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(244, 247, 251));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(18), dp(24), dp(18));
        scroll.addView(root, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);

        TextView title = text("兜风 Designer 参数探测 v1.1", 28,
                Color.rgb(28, 39, 55), true);
        root.addView(title, lpMatch(dp(50)));

        TextView sub = text(
                "你已经确认 DesignerActivity 能打开；现在只测试它要求的 designerId / refSource / ref 参数格式。",
                16, Color.rgb(88, 104, 126), false);
        LinearLayout.LayoutParams slp = lpMatch(dp(54));
        slp.bottomMargin = dp(12);
        root.addView(sub, slp);

        status = text(dofunInfo(), 14, Color.rgb(66, 82, 105), false);
        status.setPadding(dp(14), dp(10), dp(14), dp(10));
        status.setBackground(round(Color.WHITE, 14));
        LinearLayout.LayoutParams st = lpMatch(dp(60));
        st.bottomMargin = dp(14);
        root.addView(status, st);

        addQuery(root, "A  数字参数：1 / 1 / 1", "1", "1", "1");
        addQuery(root, "B  首页来源：1 / home / home", "1", "home", "home");
        addQuery(root, "C  主题来源：1 / theme / theme", "1", "theme", "theme");
        addQuery(root, "D  在线来源：1 / online / online", "1", "online", "online");
        addQuery(root, "E  设计师来源：1 / designer / designer", "1", "designer", "designer");
        addQuery(root, "F  全 0：0 / 0 / 0", "0", "0", "0");

        TextView g = button("G  显式 Activity + String extras");
        g.setOnClickListener(v -> openExplicitStrings("1", "theme", "theme"));
        root.addView(g, buttonLp());

        TextView h = button("H  显式 Activity + Integer extras");
        h.setOnClickListener(v -> openExplicitInts(1, 1, 1));
        root.addView(h, buttonLp());

        TextView i = button("I  Query + extras 同时发送");
        i.setOnClickListener(v -> openBoth("1", "theme", "theme"));
        root.addView(i, buttonLp());

        TextView normal = button("J  返回兜风");
        normal.setOnClickListener(v -> openPackage());
        root.addView(normal, buttonLp());

        TextView note = text(
                "测试方法：从 A 开始逐个点。只要有一个不再出现“designerId=null, refSource=null, ref=null”，"
                + "就拍下新的提示或页面给我。即使变成“设计师不存在/网络错误”也很有价值。",
                15, Color.rgb(52, 66, 86), false);
        note.setPadding(dp(14), dp(12), dp(14), dp(12));
        note.setBackground(round(Color.rgb(232, 241, 255), 14));
        LinearLayout.LayoutParams nlp = lpMatch(dp(90));
        nlp.topMargin = dp(6);
        root.addView(note, nlp);
    }

    private void addQuery(LinearLayout root, String label, String designerId,
                          String refSource, String ref) {
        TextView b = button(label);
        b.setOnClickListener(v -> openQuery(designerId, refSource, ref));
        root.addView(b, buttonLp());
    }

    private void openQuery(String designerId, String refSource, String ref) {
        Uri uri = Uri.parse(BASE).buildUpon()
                .appendQueryParameter("designerId", designerId)
                .appendQueryParameter("refSource", refSource)
                .appendQueryParameter("ref", ref)
                .build();
        Intent i = new Intent(Intent.ACTION_VIEW, uri);
        i.setPackage(DOFUN);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        launch(i, "Query: " + uri);
    }

    private void openExplicitStrings(String designerId, String refSource, String ref) {
        Intent i = new Intent();
        i.setClassName(DOFUN, DESIGNER);
        i.putExtra("designerId", designerId);
        i.putExtra("refSource", refSource);
        i.putExtra("ref", ref);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        launch(i, "String extras: " + designerId + "/" + refSource + "/" + ref);
    }

    private void openExplicitInts(int designerId, int refSource, int ref) {
        Intent i = new Intent();
        i.setClassName(DOFUN, DESIGNER);
        i.putExtra("designerId", designerId);
        i.putExtra("refSource", refSource);
        i.putExtra("ref", ref);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        launch(i, "Integer extras: " + designerId + "/" + refSource + "/" + ref);
    }

    private void openBoth(String designerId, String refSource, String ref) {
        Uri uri = Uri.parse(BASE).buildUpon()
                .appendQueryParameter("designerId", designerId)
                .appendQueryParameter("refSource", refSource)
                .appendQueryParameter("ref", ref)
                .build();
        Intent i = new Intent(Intent.ACTION_VIEW, uri);
        i.setPackage(DOFUN);
        i.putExtra("designerId", designerId);
        i.putExtra("refSource", refSource);
        i.putExtra("ref", ref);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        launch(i, "Query + extras");
    }

    private void launch(Intent i, String desc) {
        try {
            startActivity(i);
            setStatus("已发送：" + desc);
        } catch (ActivityNotFoundException e) {
            setStatus("未找到入口：" + desc);
        } catch (SecurityException e) {
            setStatus("被权限阻止：" + desc);
        } catch (RuntimeException e) {
            setStatus("打开失败：" + e.getClass().getSimpleName());
        }
    }

    private void openPackage() {
        Intent i = getPackageManager().getLaunchIntentForPackage(DOFUN);
        if (i == null) {
            setStatus("未检测到 " + DOFUN);
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
            return "兜风：" + p.versionName + "    " + DOFUN;
        } catch (Exception e) {
            return "未检测到兜风：" + DOFUN;
        }
    }

    private void setStatus(String s) {
        if (status != null) status.setText(s);
    }

    private TextView button(String s) {
        TextView v = text(s, 17, Color.rgb(27, 66, 126), true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(18), 0, dp(18), 0);
        v.setBackground(round(Color.WHITE, 15));
        return v;
    }

    private LinearLayout.LayoutParams buttonLp() {
        LinearLayout.LayoutParams lp = lpMatch(dp(56));
        lp.bottomMargin = dp(9);
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
print("Patched DoFun Designer parameter probe v1.1.")
