#!/usr/bin/env python3
"""Render the 9-card promo carousel (1080x1440) from template.html.

template.html is the single source of the look: background streaks, type scale,
spacing and the glass chips. This script reuses its <style> and background
markup, fills in each card's text from SLIDES below, and screenshots every card
with headless Chrome into slides/01.png ... slides/09.png.

Usage:
  python3 assets/promo/build.py [--chrome PATH]
"""
import argparse
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = (HERE / "template.html").read_text(encoding="utf-8")
STYLE = re.search(r"<style>(.*?)</style>", TEMPLATE, re.S).group(1).replace(
    ".chips { margin-top: 72px; display: flex; gap: 16px; }",
    ".chips { margin-top: 72px; display: flex; flex-wrap: wrap; gap: 16px; }",
)
STREAKS = re.search(r'(<div class="s s4"></div>.*?<div class="s s6"></div>)', TEMPLATE, re.S).group(1)
BRAND = "github.com/songth1ef/agent-memory-nest"
HANDLE = "歌贼王 @songth1ef"

# Each card: kicker, title (soft line, strong line), body (lead, detail), chips.
# Keep the strong title line to about 6 Chinese characters so it fits one line.
SLIDES = [
    dict(kicker="半年实战分享", soft="我用了半年的", strong="AI 记忆系统",
         lead="一个 git 仓库",
         detail="喂饱 <b>10 台机器</b>上的 <b>30+ 个 agent</b><br>换电脑、换厂商、被封号，记忆都不丢。",
         chips=["跨设备", "跨厂商", "记忆自持", "开源"]),
    dict(kicker="你一定遇到过", soft="AI 的记忆", strong="被锁死了",
         lead="换台电脑，从零开始",
         detail="Claude 学到的，Codex 不知道。<br>订阅到期、<b>账号被封</b>，积累一夜清零。",
         chips=["锁在机器上", "锁在厂商里", "锁在账号里"]),
    dict(kicker="解法只有一句话", soft="把记忆放进", strong="自己的 git 仓库",
         lead="规则 · 记忆 · 上下文",
         detail="每个 agent 开工前读，干完活写回。<br>拉取、提交、推送，<b>全部自动</b>。",
         chips=["私有仓库", "纯 markdown", "自动同步"]),
    dict(kicker="跨厂商 · 跨设备", soft="换工具、换电脑", strong="上下文不变",
         lead="同一个巢，这些工具一起读写",
         detail="台式机开始的活，<b>笔记本接着写</b>，<br>服务器上的 agent 通宵跑测试。",
         chips=["Claude Code", "Codex", "Gemini CLI", "Kimi Code", "Hermes", "Antigravity"]),
    dict(kicker="极易上手", soft="不用服务器", strong="不用常驻进程",
         lead="只要一个私有 git 仓库",
         detail="把一段提示词粘贴给你的 agent，<br><b>它会自己装好</b>，之后照常使用。",
         chips=["0 服务器", "0 端口", "0 新命令"]),
    dict(kicker="天生私密", soft="加密之后", strong="托管方读不到",
         lead="连 GitHub 都读不到记忆内容",
         detail="agent 读写明文，仓库里只存密文。<br>私有巢想推到公开仓库？<b>git 直接拒绝</b>。",
         chips=["git-crypt", "防误推护栏", "私有仓库"]),
    dict(kicker="为什么值得长期记", soft="给 AI 写记忆", strong="复利最高的事",
         lead="每一次纠正，只讲一遍",
         detail="记得越多，越懂你的习惯和项目。<br>积累属于你，<b>不随工具和账号消失</b>。",
         chips=["越用越顺手", "少反复纠错", "积累归你"]),
    dict(kicker="记忆越多，启动越轻", soft="只加载", strong="任务需要的",
         lead="常驻一小层摘要，其余按需检索",
         detail="实测默认启动约 <b>1,600 token</b><br>全量加载约 79,000，<b>只读约 1/50</b>。",
         chips=["常驻摘要", "按需检索", "上下文不膨胀"]),
    dict(kicker="开源 · MIT", soft="来试试", strong="欢迎 Star",
         lead="复制一段提示词，就能装好",
         detail="从 2026 年 4 月起每天在用：<br><b>10 台机器 · 10 种工具 · 30+ 个 agent</b>",
         chips=["跨设备", "跨厂商", "记忆自持", "开源"]),
]


def render(index: int, slide: dict, total: int) -> str:
    chips = "".join(f'<div class="chip"><span>{c}</span></div>' for c in slide["chips"])
    dots = "".join('<i class="on"></i>' if i == index else "<i></i>" for i in range(total))
    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><style>{STYLE}</style></head>
<body>
{STREAKS}
<div class="wrap">
  <div class="top"><div class="brand">{BRAND}</div><div class="page">{index + 1} / {total}</div></div>
  <div class="main">
    <div class="kicker">{slide['kicker']}</div>
    <h1><span class="soft">{slide['soft']}</span><br>{slide['strong']}</h1>
    <div class="body"><div class="lead">{slide['lead']}</div><div class="detail">{slide['detail']}</div></div>
    <div class="chips">{chips}</div>
  </div>
  <div class="foot"><div class="handle">{HANDLE}</div><div class="dots">{dots}</div></div>
</div>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chrome", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    args = parser.parse_args()
    out = HERE / "slides"
    out.mkdir(exist_ok=True)
    for i, slide in enumerate(SLIDES):
        page = out / f"{i + 1:02d}.html"
        page.write_text(render(i, slide, len(SLIDES)), encoding="utf-8")
        png = page.with_suffix(".png")
        subprocess.run([args.chrome, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=1080,1440", f"--screenshot={png}", page.as_uri()],
                       check=True, capture_output=True, timeout=60)
        print("rendered", png.relative_to(HERE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
