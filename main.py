"""
Temp Mail via tempmail.lol API
"""
import time
import json
import random
import string
import re
import os
import requests
import whisper
import tempfile
import subprocess
import numpy as np
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

XIAOMI_URL = "https://global.account.xiaomi.com/fe/service/register"
MAIL_API = "https://api.tempmail.lol/v2"

def gen_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = [random.choice(string.ascii_uppercase), random.choice(string.ascii_lowercase),
           random.choice(string.digits), random.choice("!@#$%^&*")]
    pwd += [random.choice(chars) for _ in range(8)]
    random.shuffle(pwd)
    return ''.join(pwd)

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def timer_start():
    return time.time()

def timer_end(start, label):
    elapsed = time.time() - start
    log(f"[TIMER] {label}: {elapsed:.1f}s")

class TempMailAPI:
    """Temp mail via tempmail.lol API"""
    
    def __init__(self):
        self.email = None
        self.token = None
    
    def create_account(self):
        """Buat temporary email address via tempmail.lol"""
        log("Creating temp mail address via tempmail.lol...")
        
        # Create inbox via API
        resp = requests.post(f"{MAIL_API}/inbox/create", timeout=15)
        
        if resp.status_code != 201:
            log(f"Failed to create email: {resp.status_code}")
            return None
        
        data = resp.json()
        self.email = data.get('address')
        self.token = data.get('token')
        
        log(f"Email created: {self.email}")
        return self.email
    
    def wait_for_message(self, keyword="xiaomi", timeout=120):
        """Tunggu email masuk dengan keyword tertentu"""
        log(f"Waiting for email containing '{keyword}'...")
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                # tempmail.lol API - get mails using token
                r = requests.get(
                    f"{MAIL_API}/inbox",
                    params={"token": self.token},
                    timeout=10
                )
                
                if r.status_code == 200:
                    data = r.json()
                    emails = data.get('emails', [])
                    
                    for mail in emails:
                        subject = mail.get('subject', '').lower()
                        body = mail.get('body', '').lower()
                        if keyword in subject or keyword in body:
                            log(f"Found email: {mail.get('subject')}")
                            return mail
                
                elapsed = int(time.time() - start)
                if elapsed % 15 == 0:
                    log(f"Waiting for email... ({elapsed}s/{timeout}s)")
                time.sleep(5)
                
            except Exception as e:
                log(f"API error: {e}")
                time.sleep(5)
        
        return None
    
    def extract_verification_code(self, message):
        """Ekstrak kode verifikasi dari email"""
        if not message:
            return None
        
        # Combine all text
        text = str(message.get('subject', '')) + " " + str(message.get('body', '')) + " " + str(message.get('html', ''))
        
        # Cari 6 digit code
        codes = re.findall(r'\b(\d{6})\b', text)
        valid = [c for c in codes if not c.startswith('20') and c != '135792']
        
        if valid:
            log(f"Verification code: {valid[0]}")
            return valid[0]
        
        # Cari pattern verification code
        patterns = [
            r'verification code[:\s]*(\d{6})',
            r'code[:\s]*(\d{6})',
            r'verify[:\s]*(\d{6})',
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                log(f"Verification code: {match.group(1)}")
                return match.group(1)
        
        log("Could not find verification code in email")
        log(f"Email text: {text[:300]}")
        return None


class XiaomiAuto:
    def __init__(self):
        self.driver = None
        self.temp_email = None
        self.password = None
        self.temp_mail = None
        
    def setup_browser(self, with_extension=False):
        log(f"Setting up browser (extension={'ON' if with_extension else 'OFF'})...")
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Randomize window size slightly
        w, h = 1920 + random.randint(-20, 20), 1080 + random.randint(-10, 10)
        options.add_argument(f'--window-size={w},{h}')
        
        # Stealth: remove automation flags
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        
        # Performance - keep only safe ones
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-translate')
        
        # Page load strategy - eager is faster but still loads DOM
        options.page_load_strategy = 'eager'
        
        if with_extension:
            ext_path = os.path.abspath(BUSTER_EXTENSION_DIR)
            if os.path.exists(ext_path):
                options.add_argument(f'--load-extension={ext_path}')
                log(f"Loading extension from: {ext_path}")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Stealth: inject advanced JS to hide automation
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                // Hide webdriver
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                
                // Fake plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ]
                });
                
                // Fake languages
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                
                // Fake platform
                Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                
                // Hardware concurrency (realistic)
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                
                // Device memory
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                
                // Fix chrome object
                window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
                
                // Fix permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
                );
                
                // WebGL vendor/renderer spoofing
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(param) {
                    if (param === 37445) return 'Intel Inc.';
                    if (param === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter.apply(this, arguments);
                };
                
                // Screen depth
                Object.defineProperty(screen, 'colorDepth', {get: () => 24});
                Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
                Object.defineProperty(screen, 'availWidth', {get: () => screen.width});
                Object.defineProperty(screen, 'availHeight', {get: () => screen.height - 40});
                
                // Connection (realistic)
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    })
                });
                
                // Remove webdriver traces from document
                document.documentElement.removeAttribute('webdriver');
                
                // Override toString to pass checks
                window.navigator.toString = () => '[object Navigator]';
            '''
        })
        
        # Set realistic timezone
        self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': 'Asia/Jakarta'
        })
        
        log("Browser started with stealth!")
    
    def wait_for_page(self, timeout=10):
        """Wait for page to be ready"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except:
            pass
    
    def human_type(self, element, text):
        """Type like a human - variable speed with random pauses"""
        element.clear()
        i = 0
        while i < len(text):
            char = text[i]
            element.send_keys(char)
            
            # Random delay - faster for common chars, slower for special
            if char in 'aeiou ':
                delay = random.uniform(0.02, 0.08)  # Vowels faster
            elif char.isupper():
                delay = random.uniform(0.05, 0.12)  # Uppercase slightly slower
            elif char in '!@#$%^&*':
                delay = random.uniform(0.08, 0.15)  # Special chars slower
            else:
                delay = random.uniform(0.03, 0.10)
            
            # Occasional longer pause (like thinking)
            if random.random() < 0.05:
                delay += random.uniform(0.2, 0.5)
            
            time.sleep(delay)
            i += 1
    
    def random_mouse_move(self):
        """Move mouse randomly to look human"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            x = random.randint(100, 800)
            y = random.randint(100, 500)
            actions.move_by_offset(x, y).pause(random.uniform(0.1, 0.3)).perform()
            actions = ActionChains(self.driver)
            actions.move_by_offset(-x, -y).perform()
        except:
            pass
    
    def fill_form(self, referral_code=None):
        log("Opening Xiaomi registration...")
        self.driver.get(XIAOMI_URL)
        self.wait_for_page(8)
        time.sleep(random.uniform(1.5, 2.5))
        
        self.password = gen_password()
        log(f"Password: {self.password}")
        
        self.random_mouse_move()
        
        # Type email like human
        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
        self.driver.execute_script("arguments[0].click();", email_input)
        time.sleep(random.uniform(0.2, 0.5))
        self.human_type(email_input, self.temp_email)
        time.sleep(random.uniform(0.3, 0.7))
        
        # Tab to password, type like human
        email_input.send_keys(Keys.TAB)
        time.sleep(random.uniform(0.2, 0.4))
        pass_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        self.driver.execute_script("arguments[0].click();", pass_input)
        time.sleep(random.uniform(0.1, 0.3))
        self.human_type(pass_input, self.password)
        time.sleep(random.uniform(0.3, 0.7))
        
        # Tab to confirm password, type like human
        pass_input.send_keys(Keys.TAB)
        time.sleep(random.uniform(0.2, 0.4))
        confirm_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='repassword']")
        self.driver.execute_script("arguments[0].click();", confirm_input)
        time.sleep(random.uniform(0.1, 0.3))
        self.human_type(confirm_input, self.password)
        time.sleep(random.uniform(0.3, 0.7))
        
        self.random_mouse_move()
        
        # Enter referral code if provided
        if referral_code:
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed():
                        placeholder = inp.get_attribute("placeholder") or ""
                        name = inp.get_attribute("name") or ""
                        if any(w in placeholder.lower() for w in ['referral', 'refer', 'code', 'invite']):
                            self.driver.execute_script("arguments[0].click();", inp)
                            time.sleep(random.uniform(0.2, 0.4))
                            self.human_type(inp, referral_code)
                            log(f"Referral code entered: {referral_code}")
                            break
                        elif any(w in name.lower() for w in ['referral', 'refer', 'code', 'invite']):
                            self.driver.execute_script("arguments[0].click();", inp)
                            time.sleep(random.uniform(0.2, 0.4))
                            self.human_type(inp, referral_code)
                            log(f"Referral code entered: {referral_code}")
                            break
            except Exception as e:
                log(f"Referral input error: {e}")
        
        try:
            checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            if not checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", checkbox)
        except:
            pass
        
        self.driver.save_screenshot("screenshots/xiaomi_filled.png")
        log("Form filled!")
    
    def click_next(self):
        log("Clicking Next...")
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and "next" in btn.text.lower():
                    self.driver.execute_script("arguments[0].click();", btn)
                    log("Next clicked!")
                    self.wait_for_page(5)
                    time.sleep(2)
                    
                    # Check for rate limit error
                    for _ in range(3):
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "too many" in body_text.lower() or "frequent attempts" in body_text.lower():
                            log("RATE LIMITED! Waiting 60 seconds...")
                            time.sleep(60)
                            # Try clicking Next again
                            buttons2 = self.driver.find_elements(By.TAG_NAME, "button")
                            for btn2 in buttons2:
                                if btn2.is_displayed() and "next" in btn2.text.lower():
                                    self.driver.execute_script("arguments[0].click();", btn2)
                                    log("Next clicked (retry)!")
                                    self.wait_for_page(5)
                                    time.sleep(2)
                                    break
                        else:
                            break
                    
                    # Check for image CAPTCHA
                    for captcha_attempt in range(3):
                        time.sleep(1)
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "enter verification code" in body_text.lower() or "verification code" in body_text.lower() or "enter captcha" in body_text.lower():
                            log(f"Image CAPTCHA detected (attempt {captcha_attempt+1}/3)!")
                            captcha_result = self.solve_image_captcha()
                            if captcha_result:
                                log(f"Image CAPTCHA solved: {captcha_result}")
                                time.sleep(2)
                                # Check if still on CAPTCHA (wrong code)
                                body_text2 = self.driver.find_element(By.TAG_NAME, "body").text
                                if "enter verification code" in body_text2.lower() or "enter captcha" in body_text2.lower():
                                    log("CAPTCHA still showing - wrong code, retrying...")
                                    continue
                                else:
                                    log("CAPTCHA gone - success!")
                                    break
                            else:
                                log("CAPTCHA solve failed, retrying...")
                                continue
                        else:
                            break
                    
                    return True
            return False
        except Exception as e:
            log(f"Next error: {e}")
            return False
    
    def solve_recaptcha_audio(self, model=None):
        """Solve reCAPTCHA via audio challenge using Whisper"""
        log("Solving reCAPTCHA with Whisper...")
        
        # Load model hanya jika belum ada
        if model is None:
            log("Loading Whisper model (tiny)...")
            model = whisper.load_model("tiny")
            log("Whisper ready!")
        
        # Step 1: Klik checkbox
        for attempt in range(15):
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                src = frame.get_attribute("src") or ""
                if "recaptcha" in src.lower() and "anchor" in src.lower():
                    try:
                        self.driver.switch_to.frame(frame)
                        checkbox = self.driver.find_element(By.CSS_SELECTOR, "#recaptcha-anchor")
                        
                        # Cek status dulu
                        classes = checkbox.get_attribute("class") or ""
                        is_checked = "recaptcha-checkbox-checked" in classes
                        if is_checked:
                            log("Already solved!")
                            self.driver.switch_to.default_content()
                            return True
                        
                        # Klik checkbox
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        log("Checkbox clicked!")
                        time.sleep(3)
                        
                        # Cek apakah solved
                        classes = checkbox.get_attribute("class") or ""
                        is_checked = "recaptcha-checkbox-checked" in classes
                        if is_checked:
                            log("Solved without challenge!")
                            self.driver.switch_to.default_content()
                            return True
                        
                        self.driver.switch_to.default_content()
                        
                        # Step 2: Jika muncul challenge, klik audio
                        log("Challenge appeared, trying audio...")
                        time.sleep(1)
                        
                        # Cari challenge frame
                        for f in self.driver.find_elements(By.TAG_NAME, "iframe"):
                            s = f.get_attribute("src") or ""
                            if "recaptcha" in s.lower() and "bframe" in s.lower():
                                self.driver.switch_to.frame(f)
                                time.sleep(1)
                                
                                # Klik tombol audio
                                audio_btn = None
                                for sel in ["#recaptcha-audio-button", ".rc-button-audio", "[aria-label*='audio']"]:
                                    try:
                                        audio_btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                                        if audio_btn.is_displayed():
                                            break
                                    except:
                                        audio_btn = None
                                
                                if audio_btn:
                                    self.driver.execute_script("arguments[0].click();", audio_btn)
                                    log("Audio button clicked!")
                                    time.sleep(2)
                                    
                                    # Step 3: Dapatkan URL audio
                                    audio_url = None
                                    try:
                                        audio_source = self.driver.find_element(By.CSS_SELECTOR, "#audio-source audio source")
                                        audio_url = audio_source.get_attribute("src")
                                    except:
                                        try:
                                            audio_el = self.driver.find_element(By.CSS_SELECTOR, "#audio-source")
                                            audio_url = audio_el.get_attribute("src")
                                        except:
                                            pass
                                    
                                    if not audio_url:
                                        log("Could not find audio URL!")
                                        self.driver.switch_to.default_content()
                                        return False
                                    
                                    log(f"Audio URL: {audio_url[:80]}...")
                                    
                                    # Step 4: Download audio
                                    try:
                                        audio_resp = requests.get(audio_url, timeout=15)
                                        if audio_resp.status_code != 200:
                                            log(f"Failed to download audio: {audio_resp.status_code}")
                                            self.driver.switch_to.default_content()
                                            return False
                                        
                                        # Save to temp file
                                        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                                            tmp.write(audio_resp.content)
                                            audio_path = tmp.name
                                        
                                        log(f"Audio downloaded: {len(audio_resp.content)} bytes")
                                    except Exception as e:
                                        log(f"Download error: {e}")
                                        self.driver.switch_to.default_content()
                                        return False
                                    
                                    # Step 5: Transcribe dengan Whisper
                                    try:
                                        log("Transcribing with Whisper...")
                                        result = model.transcribe(audio_path)
                                        transcript = result["text"].strip()
                                        log(f"Transcribed: {transcript}")
                                        
                                        # Clean up temp file
                                        os.unlink(audio_path)
                                    except Exception as e:
                                        log(f"Whisper error: {e}")
                                        try:
                                            os.unlink(audio_path)
                                        except:
                                            pass
                                        self.driver.switch_to.default_content()
                                        return False
                                    
                                    # Step 6: Input jawaban
                                    try:
                                        answer_input = self.driver.find_element(By.CSS_SELECTOR, "#audio-response")
                                        answer_input.clear()
                                        # Hapus spasi/characters yang tidak perlu
                                        clean_answer = re.sub(r'[^a-zA-Z0-9\s]', '', transcript).strip()
                                        answer_input.send_keys(clean_answer)
                                        log(f"Answer entered: {clean_answer}")
                                        time.sleep(0.5)
                                    except Exception as e:
                                        log(f"Input error: {e}")
                                        self.driver.switch_to.default_content()
                                        return False
                                    
                                    # Step 7: Klik verify
                                    try:
                                        verify_btn = self.driver.find_element(By.CSS_SELECTOR, "#recaptcha-verify-button")
                                        self.driver.execute_script("arguments[0].click();", verify_btn)
                                        log("Verify clicked!")
                                        time.sleep(3)
                                    except Exception as e:
                                        log(f"Verify error: {e}")
                                        self.driver.switch_to.default_content()
                                        return False
                                    
                                    # Step 8: Cek apakah solved
                                    log("Checking if CAPTCHA solved...")
                                    time.sleep(2)
                                    
                                    # Check if "Multiple correct solutions required" appears
                                    try:
                                        bframe = None
                                        for ff in self.driver.find_elements(By.TAG_NAME, "iframe"):
                                            ss = ff.get_attribute("src") or ""
                                            if "recaptcha" in ss.lower() and "bframe" in ss.lower():
                                                bframe = ff
                                                break
                                        
                                        if bframe:
                                            self.driver.switch_to.frame(bframe)
                                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                                            self.driver.switch_to.default_content()
                                            
                                            if "multiple correct" in page_text:
                                                log("Multiple solutions required - solving again...")
                                                time.sleep(1)
                                                # Loop akan otomatis coba lagi (continue)
                                                continue
                                    except:
                                        self.driver.switch_to.default_content()
                                    
                                    # Method 1: Check via anchor frame
                                    solved = False
                                    try:
                                        self.driver.switch_to.default_content()
                                        for ff in self.driver.find_elements(By.TAG_NAME, "iframe"):
                                            ss = ff.get_attribute("src") or ""
                                            if "recaptcha" in ss.lower() and "anchor" in ss.lower():
                                                self.driver.switch_to.frame(ff)
                                                time.sleep(0.5)
                                                try:
                                                    anc = self.driver.find_element(By.CSS_SELECTOR, "#recaptcha-anchor")
                                                    cls = anc.get_attribute("class") or ""
                                                    log(f"Checkbox classes: {cls}")
                                                    if "recaptcha-checkbox-checked" in cls:
                                                        solved = True
                                                        log("Solved after Whisper!")
                                                except Exception as e:
                                                    log(f"Check error: {e}")
                                                self.driver.switch_to.default_content()
                                                break
                                    except Exception as e:
                                        log(f"Frame check error: {e}")
                                        self.driver.switch_to.default_content()
                                    
                                    if solved:
                                        return True
                                    
                                    # Method 2: Check if challenge frame is gone (indicates solved)
                                    try:
                                        challenge_frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='bframe']")
                                        if not challenge_frames:
                                            log("Challenge frame gone - likely solved!")
                                            return True
                                    except:
                                        pass
                                    
                                    # Method 3: Check page for next/submit button
                                    try:
                                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                                        for btn in buttons:
                                            if btn.is_displayed():
                                                text = btn.text.lower()
                                                if any(w in text for w in ['next', 'submit', 'sign up', 'register']):
                                                    log(f"Found submit button - CAPTCHA likely solved!")
                                                    return True
                                    except:
                                        pass
                                    
                                    log("Not solved yet, retrying...")
                                    time.sleep(2)
                                    continue
                                else:
                                    log("Audio button not found")
                                    self.driver.switch_to.default_content()
                                    return False
                        
                        return False
                    except Exception as e:
                        log(f"Frame error: {e}")
                        self.driver.switch_to.default_content()
            
            log(f"Waiting for reCAPTCHA... ({attempt+1}/15)")
            time.sleep(2)
        
        log("reCAPTCHA not found")
        return False
    
    def solve_image_captcha(self):
        """Solve image CAPTCHA using tesseract subprocess"""
        log("Checking for image CAPTCHA...")
        time.sleep(2)
        
        # Check if image CAPTCHA modal appeared
        try:
            # Look for "Enter verification code" modal
            modals = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Enter verification code')]")
            if not modals:
                log("No image CAPTCHA found")
                return None
            
            log("Image CAPTCHA detected!")
            self.driver.save_screenshot("screenshots/captcha_modal.png")
            
            # Find CAPTCHA image
            img_element = None
            try:
                img_elements = self.driver.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    if img.is_displayed():
                        src = img.get_attribute("src") or ""
                        # Skip small icons
                        width = img.size.get('width', 0)
                        if width > 50 and ('captcha' in src.lower() or 'verify' in src.lower() or len(src) > 50):
                            img_element = img
                            break
                
                if not img_element:
                    # Try finding any visible image that's not an icon
                    for img in img_elements:
                        if img.is_displayed():
                            width = img.size.get('width', 0)
                            if width > 80:  # CAPTCHA images are usually larger
                                img_element = img
                                break
            except Exception as e:
                log(f"Find image error: {e}")
            
            if not img_element:
                log("Could not find CAPTCHA image")
                return None
            
            # Download and process image
            try:
                src = img_element.get_attribute("src")
                if src.startswith("data:"):
                    import base64
                    data = src.split(",")[1]
                    img_data = base64.b64decode(data)
                else:
                    img_data = requests.get(src).content
                
                log("Reading CAPTCHA with tesseract...")
                
                pil_img = Image.open(BytesIO(img_data))
                pil_img.save("screenshots/captcha_original.png")
                
                # Convert to OpenCV format
                import cv2
                import numpy as np
                img_arr = np.array(pil_img)
                if len(img_arr.shape) == 3:
                    bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img_arr
                
                # Resize
                gray = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
                
                output_path = "screenshots/captcha_output"
                captcha_text = ""
                
                # Method 1: Adaptive threshold
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                cv2.imwrite("screenshots/captcha_adaptive.png", adaptive)
                
                # Method 2: Otsu threshold
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                cv2.imwrite("screenshots/captcha_otsu.png", otsu)
                
                # Method 3: Median blur + threshold
                blurred = cv2.medianBlur(gray, 3)
                _, median_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                cv2.imwrite("screenshots/captcha_median.png", median_thresh)
                
                # Method 4: Morphological - remove noise
                kernel = np.ones((2,2), np.uint8)
                morph = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel)
                cv2.imwrite("screenshots/captcha_morph.png", morph)
                
                # Method 5: Inverted adaptive
                inv_adaptive = cv2.bitwise_not(adaptive)
                cv2.imwrite("screenshots/captcha_inv.png", inv_adaptive)
                
                methods = [
                    ("adaptive", adaptive),
                    ("otsu", otsu),
                    ("median", median_thresh),
                    ("morph", morph),
                    ("inv", inv_adaptive),
                ]
                
                for name, img in methods:
                    temp_path = f"screenshots/captcha_{name}.png"
                    cv2.imwrite(temp_path, img)
                    
                    for psm in ['7', '8', '13', '6', '10']:
                        result = subprocess.run(
                            [TESSERACT_CMD, temp_path, output_path, '--psm', psm,
                             '-c', 'tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'],
                            capture_output=True, text=True
                        )
                        try:
                            with open(output_path + ".txt", "r") as f:
                                text = f.read().strip()
                                if text and 4 <= len(text) <= 6 and text.isalnum():
                                    captcha_text = text
                                    log(f"OCR success ({name}, psm={psm}): {captcha_text}")
                                    break
                        except:
                            pass
                    if captcha_text:
                        break
                
                # Fallback: try len 3-5
                if not captcha_text:
                    for name, img in methods:
                        temp_path = f"screenshots/captcha_{name}.png"
                        for psm in ['7', '8', '13']:
                            result = subprocess.run(
                                [TESSERACT_CMD, temp_path, output_path, '--psm', psm,
                                 '-c', 'tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'],
                                capture_output=True, text=True
                            )
                            try:
                                with open(output_path + ".txt", "r") as f:
                                    text = f.read().strip()
                                    if text and 3 <= len(text) <= 6 and text.isalnum():
                                        captcha_text = text
                                        log(f"OCR fallback ({name}, psm={psm}): {captcha_text}")
                                        break
                            except:
                                pass
                        if captcha_text:
                            break
                
                if captcha_text:
                    log(f"CAPTCHA text: {captcha_text}")
                    
                    # Find input field
                    code_input = None
                    all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in all_inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            placeholder = inp.get_attribute("placeholder") or ""
                            if 'code' in placeholder.lower() or 'captcha' in placeholder.lower():
                                code_input = inp
                                break
                    
                    if not code_input:
                        for inp in all_inputs:
                            if inp.is_displayed() and inp.is_enabled():
                                inp_type = inp.get_attribute("type") or "text"
                                if inp_type in ["text", "tel", "number", ""]:
                                    code_input = inp
                                    break
                    
                    if code_input:
                        code_input.clear()
                        code_input.send_keys(captcha_text)
                        log(f"Code entered: {captcha_text}")
                        time.sleep(1)
                        
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if btn.is_displayed() and 'submit' in btn.text.lower():
                                self.driver.execute_script("arguments[0].click();", btn)
                                log("CAPTCHA submitted!")
                                time.sleep(3)
                                
                                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                                if 'enter captcha' in body_text.lower() or 'enter verification' in body_text.lower():
                                    log("CAPTCHA still showing - might be wrong code")
                                    return None
                                
                                self._image_captcha_solved = True
                                return captcha_text
                    else:
                        log("Could not find input field!")
                else:
                    log("OCR failed on all methods")
                
            except Exception as e:
                log(f"Process CAPTCHA error: {e}")
            
        except Exception as e:
            log(f"Image CAPTCHA error: {e}")
        
        return None
    
    def submit_final(self):
        log("Submitting form...")
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if any(w in text for w in ['sign up', 'register', 'create', 'submit', 'next']):
                        self.driver.execute_script("arguments[0].click();", btn)
                        log(f"Clicked: {btn.text}")
                        time.sleep(3)
                        return True
            return False
        except Exception as e:
            log(f"Submit error: {e}")
            return False
    
    def enter_code(self, code):
        log(f"Entering code: {code}")
        time.sleep(2)
        self.driver.save_screenshot("screenshots/xiaomi_verify.png")
        
        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for inp in all_inputs:
            try:
                if inp.is_displayed() and inp.is_enabled():
                    maxlength = inp.get_attribute("maxlength") or ""
                    input_type = inp.get_attribute("type") or "text"
                    
                    if maxlength == "6" or input_type in ["tel", "number"]:
                        inp.clear()
                        inp.send_keys(code)
                        log(f"Code entered!")
                        time.sleep(0.5)
                        
                        # Submit
                        btns = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in btns:
                            if btn.is_displayed():
                                text = btn.text.lower()
                                if any(w in text for w in ['verify', 'submit', 'confirm', 'next', 'continue', 'ok']):
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    log(f"Clicked: {btn.text}")
                                    time.sleep(3)
                                    return True
                        return True
            except:
                continue
        return False
    
    def extract_session(self):
        log("Extracting session tokens...")
        time.sleep(1)
        
        cookies = self.driver.get_cookies()
        log(f"Cookies: {len(cookies)}")
        
        try:
            local_storage = self.driver.execute_script("return JSON.stringify(window.localStorage);")
            ls = json.loads(local_storage) if local_storage else {}
        except:
            ls = {}
        
        try:
            session_storage = self.driver.execute_script("return JSON.stringify(window.sessionStorage);")
            ss = json.loads(session_storage) if session_storage else {}
        except:
            ss = {}
        
        session = {
            "email": self.temp_email,
            "password": self.password,
            "url": self.driver.current_url,
            "cookies": cookies,
            "localStorage": ls,
            "sessionStorage": ss,
        }
        
        with open("results/xiaomi_session.json", "w") as f:
            json.dump(session, f, indent=2, default=str)
        
        log("Session saved: results/xiaomi_session.json")
        print("\n" + "="*60)
        print(" SESSION TOKENS EXTRACTED!")
        print("="*60)
        print(f" Email: {self.temp_email}")
        print(f" Password: {self.password}")
        print(f" Cookies: {len(cookies)}")
        print(f" Full data: xiaomi_session.json")
        print("="*60)
    
    def accept_terms(self):
        """Accept Terms & Agreements on MiMo platform"""
        log("Navigating to MiMo platform...")
        self.driver.get("https://platform.xiaomimimo.com/")
        self.wait_for_page(5)
        time.sleep(2)
        
        # Cek apakah ada Terms & Agreements popup
        try:
            # Cari checkbox "I agree" - pakai class ant-checkbox-input
            checkbox = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.ant-checkbox-input[type='checkbox']")
            ))
            
            if checkbox and not checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", checkbox)
                log("Terms checkbox clicked!")
                time.sleep(1)
            
            # Klik Confirm button
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'confirm' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Confirm clicked!")
                        time.sleep(3)
                        return True
        except Exception as e:
            log(f"Terms accept error: {e}")
        
        return False
    
    def create_api_key(self):
        """Create API key on MiMo platform"""
        log("Navigating to API Keys page...")
        self.driver.get("https://platform.xiaomimimo.com/console/api-keys")
        self.wait_for_page(5)
        time.sleep(2)
        
        # Click "Create API Key" button
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'create' in text and 'api' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Create API Key clicked!")
                        time.sleep(2)
                        break
        except Exception as e:
            log(f"Create button error: {e}")
            return None
        
        # Enter API key name
        try:
            # Try multiple selectors
            name_input = None
            for sel in ["input[placeholder='Please enter']", "input[placeholder*='enter']", "input[placeholder*='name']", "input[type='text']"]:
                try:
                    name_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if name_input.is_displayed():
                        break
                    name_input = None
                except:
                    continue
            
            if not name_input:
                # Fallback: find any visible input
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        name_input = inp
                        break
            
            if name_input:
                api_key_name = f"key_{random.randint(1000, 9999)}"
                name_input.clear()
                name_input.send_keys(api_key_name)
                log(f"API key name: {api_key_name}")
                time.sleep(0.5)
            else:
                log("Could not find name input!")
                self.driver.save_screenshot("screenshots/api_key_input_debug.png")
                return None
        except Exception as e:
            log(f"Name input error: {e}")
            return None
        
        # Click Confirm
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'confirm' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Confirm clicked!")
                        time.sleep(3)
                        break
        except Exception as e:
            log(f"Confirm error: {e}")
            return None
        
        # Copy API key
        try:
            # Wait for API key to appear
            time.sleep(2)
            
            api_key = None
            
            # Method 1: Look for input with sk- pattern
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input")
            for inp in inputs:
                try:
                    val = inp.get_attribute("value") or ""
                    if val.startswith("sk-"):
                        api_key = val
                        break
                except:
                    continue
            
            # Method 2: Look for text elements with sk- pattern
            if not api_key:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'sk-')]")
                for el in elements:
                    text = el.text or ""
                    if text.startswith("sk-") and len(text) > 20:
                        api_key = text
                        break
            
            # Method 3: Look for copy button and get from nearby elements
            if not api_key:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.is_displayed():
                        text = btn.text.lower()
                        if 'copy' in text:
                            # Try to find API key in modal/dialog
                            modals = self.driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], .ant-modal, .modal")
                            for modal in modals:
                                modal_text = modal.text
                                if 'sk-' in modal_text:
                                    import re
                                    match = re.search(r'(sk-[a-zA-Z0-9]+)', modal_text)
                                    if match:
                                        api_key = match.group(1)
                                        break
                            if api_key:
                                break
            
            if api_key:
                log(f"API Key: {api_key[:30]}...")
                return api_key
            else:
                self.driver.save_screenshot("screenshots/api_key_debug.png")
                log("Could not find API key - saved debug screenshot")
                return None
                
        except Exception as e:
            log(f"Copy error: {e}")
            return None
    
    def get_referral_code(self):
        """Get referral code from Refer & earn page"""
        log("Getting referral code...")
        time.sleep(2)
        
        # Click "Refer & earn" button
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'refer' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Refer & earn clicked!")
                        time.sleep(4)
                        break
        except Exception as e:
            log(f"Refer button error: {e}")
            return None
        
        # Take screenshot for debugging
        self.driver.save_screenshot("screenshots/refer_modal.png")
        
        # Find invite code
        try:
            # Try multiple approaches to find the 6-character code (letters + numbers)
            # Approach 1: Look for elements with exactly 6 alphanumeric characters
            all_elements = self.driver.find_elements(By.XPATH, "//*[string-length(text())=6]")
            for el in all_elements:
                code = el.text.strip()
                if code.isalnum() and len(code) == 6 and any(c.isalpha() for c in code) and any(c.isdigit() for c in code):
                    log(f"Referral code found: {code}")
                    self._close_refer_modal()
                    return code
            
            # Approach 2: Look for elements containing "Invite code" and nearby code
            invite_labels = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Invite code') or contains(text(), 'invite code')]")
            for label in invite_labels:
                try:
                    parent = label.find_element(By.XPATH, "./..")
                    code_elements = parent.find_elements(By.XPATH, ".//*[string-length(text())=6]")
                    for code_el in code_elements:
                        code = code_el.text.strip()
                        if code.isalnum() and len(code) == 6:
                            log(f"Referral code found: {code}")
                            self._close_refer_modal()
                            return code
                except:
                    pass
            
            # Approach 3: Look for any 6-char alphanumeric code in page text
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            import re
            codes = re.findall(r'\b[A-Za-z0-9]{6}\b', body_text)
            # Filter: must have both letters and numbers
            for code in codes:
                if any(c.isalpha() for c in code) and any(c.isdigit() for c in code):
                    log(f"Referral code found in text: {code}")
                    self._close_refer_modal()
                    return code
                
        except Exception as e:
            log(f"Find code error: {e}")
        
        log("Could not find referral code")
        return None
    
    def _close_refer_modal(self):
        """Close the referral modal"""
        try:
            # Try various close buttons
            selectors = ["button[aria-label='close']", ".close-button", "button.modal-close"]
            for sel in selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if close_btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", close_btn)
                        time.sleep(1)
                        return
                except:
                    continue
            
            # Try X button
            x_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), '×') or contains(@class, 'close')]")
            for x in x_buttons:
                if x.is_displayed():
                    self.driver.execute_script("arguments[0].click();", x)
                    time.sleep(1)
                    return
            
            # Try Escape key
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass
    
    def _open_invite_modal(self):
        """Open the invite code modal - call once before entering multiple codes"""
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'enter invite' in text or 'invite code' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Enter invite code modal opened!")
                        time.sleep(1.5)
                        return True
        except Exception as e:
            log(f"Open invite modal error: {e}")
        return False
    
    def _enter_code_in_modal(self, code):
        """Enter a code in the invite modal"""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[maxlength='1']")
            if not inputs:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            
            visible_inputs = [inp for inp in inputs if inp.is_displayed()]
            
            if len(visible_inputs) >= 6:
                for i, char in enumerate(code[:6]):
                    visible_inputs[i].click()
                    visible_inputs[i].send_keys(Keys.CONTROL + "a")
                    visible_inputs[i].send_keys(Keys.DELETE)
                    time.sleep(0.03)
                    visible_inputs[i].send_keys(char)
                    time.sleep(0.05)
                log(f"Code entered: {code}")
                return True
            else:
                for inp in visible_inputs:
                    placeholder = inp.get_attribute("placeholder") or ""
                    if 'code' in placeholder.lower() or 'invite' in placeholder.lower() or len(visible_inputs) == 1:
                        inp.click()
                        inp.send_keys(Keys.CONTROL + "a")
                        inp.send_keys(Keys.DELETE)
                        self.human_type(inp, code)
                        log(f"Code entered: {code}")
                        return True
        except Exception as e:
            log(f"Enter code error: {e}")
        return False
    
    def _click_redeem(self):
        """Click redeem button"""
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'redeem' in text:
                        self.driver.execute_script("arguments[0].click();", btn)
                        log("Redeem clicked!")
                        time.sleep(1.5)
                        return True
        except Exception as e:
            log(f"Redeem click error: {e}")
        return False
    
    def _is_code_found_error(self):
        """Check if 'invitation code not found' error appears"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body").text
            if 'not found' in body.lower():
                return True
        except:
            pass
        return False
    
    def _is_success(self):
        """Check if redeem was successful"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body").text
            if 'success' in body.lower() or 'redeemed' in body.lower():
                return True
        except:
            pass
        return False
    
    def use_invite_codes_batch(self, codes, own_code=None):
        """Redeem the most recent code only (latest from referral_codes.json)"""
        if not codes:
            return 0
        
        valid_codes = [c for c in codes if c and c != own_code]
        if not valid_codes:
            return 0
        
        code = valid_codes[-1]
        log(f"Trying invite code: {code}")
        
        if not self._open_invite_modal():
            log("Failed to open invite modal")
            return 0
        
        if not self._enter_code_in_modal(code):
            self._close_refer_modal()
            return 0
        
        time.sleep(0.3)
        
        redeemed = 0
        if self._click_redeem():
            if self._is_success():
                redeemed = 1
                log(f"Redeem successful!")
            elif self._is_code_found_error():
                log("Code not found")
            else:
                log("Unknown result")
        
        self._close_refer_modal()
        return redeemed
    
    def use_referral_code(self, code):
        """Use referral code on registration page"""
        if not code:
            return False
            
        log(f"Using referral code: {code}")
        
        # Look for referral input field
        try:
            # Find input with referral-related placeholder
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.is_displayed():
                    placeholder = inp.get_attribute("placeholder") or ""
                    name = inp.get_attribute("name") or ""
                    if any(w in placeholder.lower() for w in ['referral', 'refer', 'code', 'invite']):
                        inp.clear()
                        inp.send_keys(code)
                        log(f"Referral code entered in input")
                        return True
                    elif any(w in name.lower() for w in ['referral', 'refer', 'code', 'invite']):
                        inp.clear()
                        inp.send_keys(code)
                        log(f"Referral code entered in input")
                        return True
            
            # Try URL parameter approach
            current_url = self.driver.current_url
            if "refer" not in current_url.lower():
                new_url = current_url + ("&" if "?" in current_url else "?") + f"refer={code}"
                self.driver.get(new_url)
                time.sleep(3)
                log("Referral code added via URL")
                return True
                
        except Exception as e:
            log(f"Use referral error: {e}")
        
        return False
    
    def save_referral_code(self, email, code):
        """Save referral code to file"""
        try:
            referrals = []
            try:
                with open("results/referral_codes.json", "r") as f:
                    referrals = json.load(f)
            except:
                pass
            
            # Add new referral
            referrals.append({
                "email": email,
                "code": code
            })
            
            with open("results/referral_codes.json", "w") as f:
                json.dump(referrals, f, indent=2)
            
            log(f"Referral code saved: {code}")
        except Exception as e:
            log(f"Save referral error: {e}")
    
    def get_random_referral_code(self):
        """Get a random referral code from saved codes"""
        try:
            with open("results/referral_codes.json", "r") as f:
                referrals = json.load(f)
            
            if referrals:
                ref = random.choice(referrals)
                return ref.get("code")
        except:
            pass
        return None
    
    def get_newest_codes(self, count=3):
        """Get newest N referral codes from saved codes"""
        codes = []
        try:
            with open("results/referral_codes.json", "r") as f:
                referrals = json.load(f)
            
            # Reverse to get newest first (assuming append = newest at end)
            for ref in reversed(referrals):
                code = ref.get("code")
                if code and code not in codes:
                    codes.append(code)
                    if len(codes) >= count:
                        break
        except:
            pass
        return codes
    
    def run_single(self, model=None):
        """Create single account"""
        t_total = timer_start()
        try:
            # Step 1: Create temp mail via API
            t = timer_start()
            self.temp_mail = TempMailAPI()
            email = self.temp_mail.create_account()
            timer_end(t, "Create email")
            if not email:
                log("FATAL: Could not create temp email!")
                return False
            
            # Step 2: Setup browser
            t = timer_start()
            self.setup_browser(with_extension=False)
            timer_end(t, "Browser setup")
            self.temp_email = email
            
            # Step 2.5: Get referral code from existing codes
            referral_code = self.get_random_referral_code()
            if referral_code:
                log(f"Using referral code: {referral_code}")
            
            # Step 3: Fill form
            t = timer_start()
            self.fill_form(referral_code)
            timer_end(t, "Fill form")
            
            # Step 4: Click Next
            t = timer_start()
            next_clicked = self.click_next()
            timer_end(t, "Click Next")
            if not next_clicked:
                log("Next not found!")
                return False
            
            # Step 5: Solve CAPTCHA (skip if image CAPTCHA was already solved)
            t = timer_start()
            if hasattr(self, '_image_captcha_solved') and self._image_captcha_solved:
                log("Image CAPTCHA already solved, skipping reCAPTCHA")
                captcha = True
            else:
                captcha = self.solve_recaptcha_audio(model)
            timer_end(t, "Solve CAPTCHA")
            if not captcha:
                log("CAPTCHA failed!")
                return False
            
            # Step 6: Submit
            t = timer_start()
            submitted = self.submit_final()
            timer_end(t, "Submit")
            if not submitted:
                log("Submit failed!")
                return False
            
            # Step 7: Wait email + enter code
            t = timer_start()
            message = self.temp_mail.wait_for_message(keyword="xiaomi", timeout=90)
            code = self.temp_mail.extract_verification_code(message) if message else None
            timer_end(t, "Wait email")
            
            if code:
                t = timer_start()
                self.enter_code(code)
                timer_end(t, "Enter code")
                time.sleep(3)
                
                # Step 8: Extract session
                t = timer_start()
                self.extract_session()
                timer_end(t, "Extract session")
                
                # Step 9: Accept Terms
                t = timer_start()
                log("Step 9: Accepting Terms...")
                self.accept_terms()
                timer_end(t, "Accept Terms")
                
                # Step 10: Get referral code
                t = timer_start()
                log("Step 10: Getting referral code...")
                new_referral = self.get_referral_code()
                if new_referral:
                    self.save_referral_code(self.temp_email, new_referral)
                timer_end(t, "Get referral code")
                
                # Step 11: Use invite codes (newest 3 only)
                t = timer_start()
                log("Step 11: Using invite codes...")
                latest_codes = self.get_newest_codes(count=3)
                redeemed = self.use_invite_codes_batch(latest_codes, new_referral)
                log(f"Redeemed: {redeemed} codes")
                timer_end(t, "Use invite codes")
                
                # Step 12: Create API Key
                t = timer_start()
                log("Step 12: Creating API Key...")
                api_key = self.create_api_key()
                timer_end(t, "Create API Key")
                
                if api_key:
                    result = {
                        "email": self.temp_email,
                        "password": self.password,
                        "api_key": api_key,
                        "referral_code": new_referral
                    }
                    with open("results/xiaomi_api_keys.json", "a") as f:
                        json.dump(result, f, indent=2)
                        f.write("\n")
                    
                    timer_end(t_total, "TOTAL")
                    print("\n" + "="*60)
                    print(" API KEY CREATED!")
                    print("="*60)
                    print(f" Email: {self.temp_email}")
                    print(f" Password: {self.password}")
                    print(f" API Key: {api_key}")
                    if new_referral:
                        print(f" Referral Code: {new_referral}")
                    print("="*60)
                    return True
            
            timer_end(t_total, "TOTAL (failed)")
            return False
            
        except Exception as e:
            log(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.save_screenshot("screenshots/error.png")
            except:
                pass
            return False
        finally:
            try:
                self.driver.quit()
            except:
                pass
    
    def run(self, count=1):
        """Create multiple accounts"""
        print("\n" + "="*60)
        print(f" XIAOMI AUTO REG - {count} ACCOUNT(S)")
        print("="*60 + "\n")
        
        # Load Whisper model SEKALI saja
        log("Loading Whisper model...")
        model = whisper.load_model("tiny")
        log("Whisper ready!")
        
        success = 0
        failed = 0
        
        for i in range(count):
            print("\n" + "="*60)
            print(f" ACCOUNT {i+1}/{count}")
            print("="*60 + "\n")
            
            if self.run_single(model):
                success += 1
                log(f"Success! ({success}/{count})")
            else:
                failed += 1
                log(f"Failed! ({failed}/{count})")
            
            # Delay between accounts to avoid rate limiting
            if i < count - 1:
                delay = random.randint(30, 60)
                log(f"Waiting {delay}s before next account...")
                time.sleep(delay)
        
        print("\n" + "="*60)
        print(f" ALL DONE! {success} success, {failed} failed")
        print("="*60)
        
        # Tampilkan semua API keys
        try:
            with open("results/xiaomi_api_keys.json", "r") as f:
                keys = f.read()
            print("\nSaved API Keys:")
            print(keys)
        except:
            pass

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    reg = XiaomiAuto()
    reg.run(count)
