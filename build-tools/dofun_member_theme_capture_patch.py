from pathlib import Path

exec(Path("build-tools/dofun_theme_capture_patch.py").read_text())

p = Path("src/launcher/src/main/java/com/cbkii/ts18launcher/LauncherActivity.java")
s = p.read_text()
s = s.replace("兜风在线主题捕获", "兜风会员主题捕获")
s = s.replace(
    "用途：只捕获你在兜风里正常下载的免费/试用主题文件，不修改兜风、不绕过购买授权。",
    "用途：测试你当前账号对会员主题的正常下载链路。只记录兜风实际下发到本机的文件，不修改会员状态、不绕过授权。"
)
s = s.replace(
    "操作顺序：1 → 2 → 在兜风里选一款官方标记“免费/试用”的主题下载完成 → 返回本工具 → 3。",
    "操作顺序：1 → 2 → 在兜风里选一款“会员主题”并正常点下载 → 返回本工具 → 3。"
)
s = s.replace(
    "基线已保存。接下来只下载官方标记为免费/试用的主题。",
    "基线已保存。接下来在兜风里选一个会员主题，按正常流程点下载。"
)
p.write_text(s)

sp = Path("src/launcher/src/main/res/values/strings.xml")
x = sp.read_text().replace("兜风在线主题捕获", "兜风会员主题捕获")
sp.write_text(x)

print("Patched member-theme capture wording.")
