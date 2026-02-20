"""
runox.io 自动续期 + 开机脚本
账号密码通过 GitHub Secrets 环境变量传入，不写死在代码里

运行方式:
    xvfb-run -a python runox_auto.py
"""

import os
import time
from seleniumbase import SB

# ── 从环境变量读取账号密码（GitHub Secrets 注入）──────────
USERNAME = os.environ.get("RUNOX_USERNAME", "")
PASSWORD = os.environ.get("RUNOX_PASSWORD", "")

if not USERNAME or not PASSWORD:
    raise ValueError("❌ 请设置环境变量 RUNOX_USERNAME 和 RUNOX_PASSWORD")

LOGIN_URL = "https://runox.io/en/"


def log(step, msg):
    print(f"[步骤 {step}] {msg}", flush=True)


def try_click(sb, selectors, timeout=6):
    """依次尝试多个 selector，成功返回 True"""
    for sel in selectors:
        try:
            sb.uc_click(sel, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def runox_auto():
    with SB(uc=True, headless=False) as sb:

        # ── 步骤 1：打开网站 ──────────────────────────────
        log(1, f"打开网站: {LOGIN_URL}")
        sb.open(LOGIN_URL)
        sb.sleep(3)

        # ── 步骤 2：点击 Log In 进入登录页 ───────────────
        log(2, "点击顶部 Log In 按钮...")
        clicked = try_click(sb, [
            "a[href*='login']",
            "//a[contains(text(),'Log In')]",
            "//button[contains(text(),'Log In')]",
        ])
        if not clicked:
            log(2, "未找到 Log In 入口，可能已在登录页，继续...")
        sb.sleep(2)

        # ── 步骤 3：输入账号密码 ──────────────────────────
        log(3, "输入账号密码...")
        for sel in ["input[type='email']", "input[name='email']",
                    "input[name='username']", "input[name='login']"]:
            try:
                sb.type(sel, USERNAME, timeout=5)
                log(3, f"账号输入成功 ({sel})")
                break
            except Exception:
                continue

        sb.type("input[type='password']", PASSWORD, timeout=10)
        log(3, "密码输入成功")
        sb.sleep(1)

        # ── 步骤 4：过 Cloudflare 人机验证 ───────────────
        log(4, "处理 Cloudflare 人机验证...")
        try:
            sb.uc_gui_click_captcha()   # PyAutoGUI 模拟真实鼠标点击验证框
            sb.sleep(3)
            sb.uc_gui_handle_captcha()  # 等待验证完成/跳转
            sb.sleep(3)
            log(4, "CF 验证完成 ✓")
        except Exception as e:
            log(4, f"CF 验证跳过（已通过或无验证）: {e}")

        # ── 步骤 5：点击 Log In 提交登录 ─────────────────
        log(5, "点击 Log In 提交登录...")
        clicked = try_click(sb, [
            "button[type='submit']",
            "input[type='submit']",
            "//button[contains(text(),'Log In')]",
            "//button[contains(text(),'Login')]",
            "//input[@value='Log In']",
        ])
        if not clicked:
            log(5, "⚠ 未找到登录提交按钮！")
            sb.save_screenshot("debug_login.png")
            raise Exception("登录按钮未找到")

        sb.sleep(5)
        log(5, f"当前页面: {sb.get_current_url()}")

        # ── 步骤 6：点击 Manage 按钮 ─────────────────────
        log(6, "寻找 Manage 按钮...")
        clicked = try_click(sb, [
            "//button[contains(text(),'Manage')]",
            "//a[contains(text(),'Manage')]",
            "a[href*='manage']",
            ".manage-btn",
            "[data-action='manage']",
        ])
        if not clicked:
            log(6, "⚠ 未找到 Manage 按钮！")
            sb.save_screenshot("debug_manage.png")
            raise Exception("Manage 按钮未找到，请检查是否登录成功")
        log(6, "Manage 按钮点击成功 ✓")
        sb.sleep(3)

        # ── 步骤 7：点击 Start / Restore 续期 ────────────
        log(7, "寻找 Start / Restore 按钮...")
        clicked = try_click(sb, [
            "//button[contains(text(),'Start / Restore')]",
            "//button[contains(text(),'Restore')]",
            "//a[contains(text(),'Start / Restore')]",
            "//a[contains(text(),'Restore')]",
            "[data-action='restore']",
            ".restore-btn",
        ])
        if clicked:
            log(7, "✅ Start / Restore 点击成功 —— 续期完成！")
        else:
            log(7, "⏰ 未找到 Start / Restore 按钮 —— 【还未到续期时间，无需操作】")
            sb.save_screenshot("debug_restore.png")
        sb.sleep(3)

        # ── 步骤 8：点击 Start 开机 ───────────────────────
        log(8, "寻找 Start 按钮（开机）...")
        clicked = try_click(sb, [
            "//button[normalize-space()='Start']",
            "//a[normalize-space()='Start']",
            "//button[contains(@class,'start') and not(contains(text(),'Restore'))]",
            "[data-action='start']",
            ".start-btn",
        ])
        if clicked:
            log(8, "✅ Start 按钮点击成功 —— 开机指令已发送！")
        else:
            log(8, "⚠ 未找到 Start 按钮（可能已在运行中）")
            sb.save_screenshot("debug_start.png")

        sb.sleep(2)
        log("✅ 完成", "全部流程执行完毕！")


if __name__ == "__main__":
    runox_auto()
