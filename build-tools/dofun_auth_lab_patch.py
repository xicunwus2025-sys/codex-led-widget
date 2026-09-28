from pathlib import Path

# Start from the existing member-theme capture implementation.
exec(Path("build-tools/dofun_member_theme_capture_patch.py").read_text())

launcher = Path("src/launcher")

# Give this combined tool its own package id.
gradle = (launcher / "build.gradle.kts").read_text()
gradle = gradle.replace('applicationId = "com.ts18.dofunthemecapture"', 'applicationId = "com.ts18.dofunauthlab"')
(launcher / "build.gradle.kts").write_text(gradle)

# App label.
sp = launcher / "src/main/res/values/strings.xml"
sp.write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">兜风会员诊断实验室</string>
</resources>
""")

p = launcher / "src/main/java/com/cbkii/ts18launcher/LauncherActivity.java"
s = p.read_text()

# Update title/description and add a local-only authorization simulator section.
s = s.replace('TextView title = text("兜风会员主题捕获"', 'TextView title = text("兜风会员诊断实验室"')
s = s.replace(
    '"用途：测试你当前账号对会员主题的正常下载链路。只记录兜风实际下发到本机的文件，不修改会员状态、不绕过授权。"',
    '"真实模式连接兜风自己的在线主题入口并记录真实下载结果；模拟模式只在本工具内部显示“已授权”，不会把模拟状态发送给兜风服务器。"'
)

needle = '''        TextView four = button("4  仅扫描最近 30 分钟文件");
        four.setOnClickListener(v -> scanRecent());
        root.addView(four, buttonLp());

        results = text('''
replacement = '''        TextView four = button("4  仅扫描最近 30 分钟文件");
        four.setOnClickListener(v -> scanRecent());
        root.addView(four, buttonLp());

        TextView sep = text("本地模拟模式（与真实服务器授权隔离）", 16,
                Color.rgb(45, 58, 78), true);
        LinearLayout.LayoutParams sepLp = lp(dp(44));
        sepLp.topMargin = dp(8);
        root.addView(sep, sepLp);

        TextView simOn = button("5  模拟：会员已授权");
        simOn.setOnClickListener(v -> {
            getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                    .putBoolean("sim_member", true)
                    .putBoolean("sim_order", true)
                    .apply();
            status.setText("模拟状态：会员=已授权，订单=已通过（仅本工具内部）。");
            results.setText("SIMULATION ONLY\\nmember=true\\norder=true\\n"
                    + "不会把这些模拟字段发送到兜风服务器，也不会用于请求受保护主题。");
        });
        root.addView(simOn, buttonLp());

        TextView simOff = button("6  模拟：恢复未授权");
        simOff.setOnClickListener(v -> {
            getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                    .putBoolean("sim_member", false)
                    .putBoolean("sim_order", false)
                    .apply();
            status.setText("模拟状态已恢复：会员=未授权，订单=未通过。");
        });
        root.addView(simOff, buttonLp());

        TextView compare = button("7  对比真实/模拟状态");
        compare.setOnClickListener(v -> {
            boolean sm = getSharedPreferences(PREFS, MODE_PRIVATE)
                    .getBoolean("sim_member", false);
            boolean so = getSharedPreferences(PREFS, MODE_PRIVATE)
                    .getBoolean("sim_order", false);
            results.setText("真实服务器状态：由兜风官方页面/下载结果决定\\n"
                    + "模拟会员=" + sm + "\\n模拟订单=" + so + "\\n"
                    + "真实模式与模拟模式互不覆盖。");
        });
        root.addView(compare, buttonLp());

        results = text('''
if needle not in s:
    raise SystemExit("UI insertion anchor not found")
s = s.replace(needle, replacement)

s = s.replace(
    '"操作顺序：1 → 2 → 在兜风里选一款“会员主题”并正常点下载 → 返回本工具 → 3。"',
    '"真实模式：1 → 2 → 在兜风里按正常账号权限操作 → 返回工具 → 3。模拟模式使用 5/6/7，仅做本地授权逻辑测试。"'
)

p.write_text(s)
print("Patched combined DoFun auth lab.")
