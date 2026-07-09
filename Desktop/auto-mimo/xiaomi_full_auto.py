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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

XIAOMI_URL = "https://global.account.xiaomi.com/fe/service/register?_locale=en_US&_uRegion=US"
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
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Performance optimizations
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-css')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-translate')
        options.add_argument('--no-first-run')
        options.add_argument('--fast')
        options.add_argument('--aggressive-cache-discard')
        
        # Page load strategy - none = fastest
        caps = options.capabilities
        caps['pageLoadStrategy'] = 'none'
        
        if with_extension:
            ext_path = os.path.abspath(BUSTER_EXTENSION_DIR)
            if os.path.exists(ext_path):
                options.add_argument(f'--load-extension={ext_path}')
                log(f"Loading extension from: {ext_path}")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        log("Browser started!")
    
    def wait_for_page(self, timeout=10):
        """Wait for page to be ready"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except:
            pass
    
    def fill_form(self):
        log("Opening Xiaomi registration...")
        self.driver.get(XIAOMI_URL)
        self.wait_for_page(8)
        time.sleep(2)
        
        self.password = gen_password()
        log(f"Password: {self.password}")
        
        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
        email_input.clear()
        email_input.send_keys(self.temp_email)
        time.sleep(0.5)
        
        pass_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pass_input.clear()
        pass_input.send_keys(self.password)
        time.sleep(0.5)
        
        confirm_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='repassword']")
        confirm_input.clear()
        confirm_input.send_keys(self.password)
        time.sleep(0.5)
        
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
                    time.sleep(1)
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
                                    return False
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
        
        with open("data/xiaomi_session.json", "w") as f:
            json.dump(session, f, indent=2, default=str)
        
        log("Session saved: data/xiaomi_session.json")
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
            
            # Step 3: Fill form
            t = timer_start()
            self.fill_form()
            timer_end(t, "Fill form")
            
            # Step 4: Click Next
            t = timer_start()
            next_clicked = self.click_next()
            timer_end(t, "Click Next")
            if not next_clicked:
                log("Next not found!")
                return False
            
            # Step 5: Solve CAPTCHA
            t = timer_start()
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
                
                # Step 10: Create API Key
                t = timer_start()
                log("Step 10: Creating API Key...")
                api_key = self.create_api_key()
                timer_end(t, "Create API Key")
                
                if api_key:
                    result = {
                        "email": self.temp_email,
                        "password": self.password,
                        "api_key": api_key
                    }
                    with open("data/xiaomi_api_keys.json", "a") as f:
                        json.dump(result, f, indent=2)
                        f.write("\n")
                    
                    timer_end(t_total, "TOTAL")
                    print("\n" + "="*60)
                    print(" API KEY CREATED!")
                    print("="*60)
                    print(f" Email: {self.temp_email}")
                    print(f" Password: {self.password}")
                    print(f" API Key: {api_key}")
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
            
            # Tunggu sebentar sebelum account berikutnya
            if i < count - 1:
                log("Waiting 3s before next account...")
                time.sleep(3)
        
        print("\n" + "="*60)
        print(f" ALL DONE! {success} success, {failed} failed")
        print("="*60)
        
        # Tampilkan semua API keys
        try:
            with open("data/xiaomi_api_keys.json", "r") as f:
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
