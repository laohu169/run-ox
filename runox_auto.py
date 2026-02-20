"""
runox.io 自动续期 + 开机脚本
参考 LunesHost 成功案例重写，使用相同的 SB 启动参数和 CF 验证方式

运行方式:
    xvfb-run -a python runox_auto.py

Secrets 配置:
    RUNOX_ACCOUNTS = email:password  （多账号用逗号分隔：a@x.com:pwd1,b@x.com:pwd2）
    TG_TOKEN       = Telegram Bot Token（可选，用于推送结果）
    TG_CHAT_ID     = Telegram Chat ID（可选）
"""

import time
import os
import random
import requests

# ── 智能环境配置（与参考代码一致）────────────────────────────
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"
if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

print(f"[DEBUG] Env DISPLAY:    {os.environ.get('DISPLAY')}")
print(f"[DEBUG] Env XAUTHORITY: {os.environ.get('XAUTHORITY')}")

from seleniumbase import SB

# ================= 配置区域 =================
PROXY_URL  = os.getenv("PROXY", "")
TG_TOKEN   = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# ===========================================

LOGIN_URL = "https://runox.io/en/login"   # 直接打开登录页，跳过首页跳转


class RunoxRenewal:
    def __init__(self, acc):
        parts = acc.strip().split(":")
        if len(parts) < 2:
            raise ValueError(f"账号格式错误，应为 email:password，收到: {acc}")
        self.email    = parts[0]
        self.password = parts[1]

        self.BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "artifacts")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        print(f"[{ts}] {msg}", flush=True)

    def human_wait(self, min_s=6, max_s=10):
        time.sleep(random.uniform(min_s, max_s))

    def shot(self, sb, name):
        path = f"{self.screenshot_dir}/{name}"
        sb.save_screenshot(path)
        self.log(f"📸 截图: {name}")
        return path

    def send_tg(self, message, photo_path=None):
        if not TG_TOKEN or not TG_CHAT_ID:
            return
        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo_path, 'rb') as f:
                    requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': message},
                                  files={'photo': f}, timeout=15)
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': message}, timeout=15)
            self.log("✅ TG 推送已发送")
        except Exception as e:
            self.log(f"⚠️ TG 推送失败: {e}")

    def run(self):
        self.log("=" * 50)
        self.log(f"🚀 开始处理账号: {self.email}")
        self.log("=" * 50)

        with SB(
            uc=True,
            test=True,
            headed=True,
            headless=False,
            xvfb=False,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--window-position=0,0,--start-maximized",
            proxy=PROXY_URL if PROXY_URL else None
        ) as sb:
            try:
                self.log("✅ 浏览器已启动")

                # ── 1. 直接打开登录页（uc_open_with_reconnect 防 CF 拦截）──
                self.log(f"📂 打开登录页: {LOGIN_URL}")
                sb.delete_all_cookies()
                sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=5)
                self.shot(sb, "01_loginpage.png")

                # ── 2. 等待并填写账号密码 ─────────────────────────────────
                self.log("✏️ 填写账号密码...")
                sb.wait_for_element_visible("#email", timeout=25)
                sb.type("#email", self.email)
                sb.type("#password", self.password)
                self.shot(sb, "02_after_input.png")

                # ── 3. 过 Cloudflare 验证 ─────────────────────────────────
                self.log("🔄 处理 Cloudflare 验证...")
                sb.uc_gui_click_captcha()
                self.human_wait(6, 10)
                sb.uc_gui_handle_captcha()
                self.human_wait(6, 10)
                self.shot(sb, "03_after_captcha.png")

                # ── 4. 点击登录按钮 ───────────────────────────────────────
                self.log("🖱️ 点击登录按钮...")
                sb.click('button.submit-btn')
                self.log("⏳ 等待登录跳转（30s）...")
                time.sleep(30)
                self.shot(sb, "04_after_login.png")
                self.log(f"📍 当前页面: {sb.get_current_url()}")

                # ── 5. 点击 Manage 按钮 ───────────────────────────────────
                self.log("🔍 寻找 Manage 按钮...")
                manage_selectors = [
                    "//button[contains(text(),'Manage')]",
                    "//a[contains(text(),'Manage')]",
                    "a[href*='manage']",
                    ".manage-btn",
                ]
                manage_ok = False
                for sel in manage_selectors:
                    try:
                        sb.wait_for_element_visible(sel, timeout=10)
                        sb.click(sel)
                        manage_ok = True
                        self.log(f"✅ Manage 点击成功 ({sel})")
                        break
                    except Exception:
                        continue

                if not manage_ok:
                    self.shot(sb, "error_no_manage.png")
                    raise Exception("未找到 Manage 按钮，登录可能未成功")

                time.sleep(5)
                self.shot(sb, "05_after_manage.png")

                # ── 6. 点击 Start / Restore 续期 ─────────────────────────
                self.log("🔍 寻找 Start / Restore 按钮...")
                restore_selectors = [
                    "//button[contains(text(),'Start / Restore')]",
                    "//button[contains(text(),'Restore')]",
                    "//a[contains(text(),'Start / Restore')]",
                    "//a[contains(text(),'Restore')]",
                ]
                restore_ok = False
                for sel in restore_selectors:
                    try:
                        sb.wait_for_element_visible(sel, timeout=8)
                        sb.click(sel)
                        restore_ok = True
                        self.log("✅ Start / Restore 点击成功 —— 续期完成！")
                        break
                    except Exception:
                        continue

                if not restore_ok:
                    self.log("⏰ 无 Start/Restore 按钮 —— 未到续期时间，跳过")
                    self.shot(sb, "06_no_restore.png")

                time.sleep(5)

                # ── 7. 点击 Start 开机 ────────────────────────────────────
                self.log("🔍 寻找 Start 按钮（开机）...")
                start_selectors = [
                    "//button[normalize-space()='Start']",
                    "//a[normalize-space()='Start']",
                    "//button[contains(text(),'Start') and not(contains(text(),'Restore'))]",
                ]
                start_ok = False
                for sel in start_selectors:
                    try:
                        sb.wait_for_element_visible(sel, timeout=8)
                        sb.click(sel)
                        start_ok = True
                        self.log("✅ Start 点击成功 —— 开机指令已发送！")
                        break
                    except Exception:
                        continue

                if not start_ok:
                    self.log("⚠️ 未找到 Start 按钮（可能已在运行中）")

                time.sleep(3)
                final = self.shot(sb, "07_final.png")

                msg = f"✅ {self.email} 保活流程完成"
                self.log(msg)
                self.send_tg(msg, final)

            except Exception as e:
                self.log(f"❌ 运行异常: {e}")
                import traceback
                traceback.print_exc()
                err_shot = self.shot(sb, "error.png")
                self.send_tg(f"❌ {self.email} 保活失败: {e}", err_shot)
                raise


if __name__ == "__main__":
    accounts = os.getenv("RUNOX_ACCOUNTS", "")
    if not accounts:
        print("❌ Error: 请设置环境变量 RUNOX_ACCOUNTS（格式: email:password）")
        exit(1)

    for acc in accounts.split(','):
        acc = acc.strip()
        if acc:
            try:
                RunoxRenewal(acc).run()
            except Exception:
                print(f"⚠️ 账号 {acc.split(':')[0]} 处理失败，继续下一个...")
