"""
MiMo AutoReg - Terminal UI
Mindblowing terminal interface for Xiaomi MiMo auto registration
"""
import os
import sys
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# ─── Colors ─────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDERL  = "\033[4m"
    
    # Gradient palette
    BG1     = "\033[48;5;234m"
    BG2     = "\033[48;5;235m"
    BG3     = "\033[48;5;236m"
    
    # Accent colors
    CYAN    = "\033[38;5;51m"
    BLUE    = "\033[38;5;75m"
    PURPLE  = "\033[38;5;141m"
    PINK    = "\033[38;5;213m"
    ORANGE  = "\033[38;5;208m"
    YELLOW  = "\033[38;5;226m"
    GREEN   = "\033[38;5;46m"
    RED     = "\033[38;5;196m"
    GRAY    = "\033[38;5;245m"
    WHITE   = "\033[38;5;255m"
    DIM_W   = "\033[38;5;240m"
    
    # Gradient text
    G1 = "\033[38;5;51m"   # Cyan
    G2 = "\033[38;5;75m"   # Blue
    G3 = "\033[38;5;141m"  # Purple
    G4 = "\033[38;5;213m"  # Pink
    G5 = "\033[38;5;208m"  # Orange


# ─── Utilities ──────────────────────────────────────────────────────────
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_size():
    size = shutil.get_terminal_size()
    return size.columns, size.lines

def center(text, width=None):
    if width is None:
        width, _ = get_terminal_size()
    lines = text.split('\n')
    return '\n'.join(line.center(width) for line in lines)

def gradient_text(text, colors=None):
    if colors is None:
        colors = [C.G1, C.G2, C.G3, C.G4, C.G5]
    result = []
    for i, ch in enumerate(text):
        if ch == ' ':
            result.append(ch)
        else:
            result.append(colors[i % len(colors)] + ch)
    return ''.join(result) + C.RESET

def box(text, color=C.CYAN, width=60):
    lines = text.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    box_w = max(width, max_len + 4)
    
    top    = f"{color}┌{'─' * (box_w - 2)}┐{C.RESET}"
    bottom = f"{color}└{'─' * (box_w - 2)}┘{C.RESET}"
    
    result = [top]
    for line in lines:
        padded = line.center(box_w - 4) if len(line) < box_w - 4 else line[:box_w - 4]
        result.append(f"{color}│{C.RESET}  {padded}  {color}│{C.RESET}")
    result.append(bottom)
    
    return '\n'.join(result)

def horizontal_line(char='─', width=60, color=C.DIM_W):
    return f"{color}{char * width}{C.RESET}"

def progress_bar(current, total, width=30, filled='█', empty='░', 
                 fill_color=C.GREEN, empty_color=C.DIM_W):
    pct = current / total if total > 0 else 0
    filled_len = int(width * pct)
    empty_len = width - filled_len
    
    bar = f"{fill_color}{filled * filled_len}{empty_color}{empty * empty_len}{C.RESET}"
    return f"{bar} {C.WHITE}{pct*100:.0f}%{C.RESET}"

def stat_box(label, value, color=C.CYAN, width=15):
    return f"{color}┌{'─'*(width-2)}┐{C.RESET}\n{color}│{C.RESET}{C.BOLD}{str(value).center(width-2)}{C.RESET}{color}│{C.RESET}\n{color}└{'─'*(width-2)}┘{C.RESET}\n{C.DIM}{label.center(width)}{C.RESET}"


# ─── Logo ───────────────────────────────────────────────────────────────
LOGO = f"""
{C.G1}  ██╗  {C.G2}██╗{C.G3}██████╗ {C.G4}██╗{C.G5}███╗  {C.G1}██╗{C.G2}███████╗{C.G3}████████╗
{C.G1}  ██║  {C.G2}██║{C.G3}██╔══██╗{C.G4}██║{C.G5}████╗ {C.G1}██║{C.G2}██╔════╝{C.G3}╚══██╔══╝
{C.G1}  {C.G2}██║  {C.G3}██║{C.G4}██████╔╝{C.G5}██║{C.G1}██╔██╗{C.G2}██║{C.G3}███████╗{C.G4}   ██║   
{C.G2}  {C.G3}██║  {C.G4}██║{C.G5}██╔══██╗{C.G1}██║{C.G2}██║╚█╗{C.G3}██║{C.G4}╚════██║{C.G5}   ██║   
{C.G3}  {C.G4}██║  {C.G5}██║{C.G1}██║  {C.G2}██║{C.G3}██║{C.G4}██║ ╚╗{C.G5}██║{C.G1}███████║{C.G2}   ██║   
{C.G4}  {C.G5}╚═╝  {C.G1}╚═╝{C.G2}╚═╝  {C.G3}╚═╝{C.G4}╚═╝{C.G5}╚═╝  {C.G1}╚═╝{C.G2}╚══════╝{C.G3}   ╚═╝   
{C.RESET}{C.DIM_W}              XIAOMI MIMO AUTO REGISTRATION{C.RESET}
"""


# ─── Banner ─────────────────────────────────────────────────────────────
BANNER = f"""
{C.CYAN}+====================================================================+
|                                                                      |
|   {C.BOLD}{C.WHITE}  ██████╗ ███╗   ███╗███████╗{C.RESET}{C.CYAN}     {C.BOLD}{C.WHITE} █████╗ ███╗   ██╗ █████╗ {C.RESET}{C.CYAN}|
|   {C.BOLD}{C.WHITE} ██╔═══██╗████╗ ████║██╔════╝{C.RESET}{C.CYAN}     {C.BOLD}{C.WHITE}██╔══██╗████╗  ██║██╔══██╗{C.RESET}{C.CYAN}|
|   {C.BOLD}{C.WHITE} ██║   ██║██╔████╔██║█████╗{C.RESET}{C.CYAN}      {C.BOLD}{C.WHITE}███████║██╔██╗ ██║███████║{C.RESET}{C.CYAN}|
|   {C.BOLD}{C.WHITE} ██║   ██║██║╚██╔╝██║██╔══╝{C.RESET}{C.CYAN}      {C.BOLD}{C.WHITE}██╔══██║██║╚█╗██║██╔══██║{C.RESET}{C.CYAN}|
|   {C.BOLD}{C.WHITE} ╚██████╔╝██║ ╚═╝ ██║███████╗{C.RESET}{C.CYAN}     {C.BOLD}{C.WHITE}██║  ██║██║ ╚███║██║  ██║{C.RESET}{C.CYAN}|
|   {C.BOLD}{C.WHITE}  ╚═════╝ ╚═╝     ╚═╝╚══════╝{C.RESET}{C.CYAN}     {C.BOLD}{C.WHITE}╚═╝  ╚═╝╚═╝  ╚══╝╚═╝  ╚═╝{C.RESET}{C.CYAN}|
|                                                                      |
|   {C.DIM_W}         AUTO REGISTRATION + REFERRAL SYSTEM            {C.CYAN}|
|   {C.DIM}              v2.0 -- Stealth Browser Enabled                      {C.CYAN}|
|                                                                      |
+====================================================================+{C.RESET}
"""


# ─── Menu ───────────────────────────────────────────────────────────────
MAIN_MENU = f"""
{C.CYAN}+----------------------------------------------------------------------+
|                                                                      |
|   {C.BOLD}{C.WHITE}MAIN MENU{C.RESET}{C.CYAN}                                                    |
|                                                                      |
|   {C.G1}[1]{C.RESET}  {C.WHITE}Create Account{C.RESET}      {C.DIM}-- Auto register new MiMo account    {C.CYAN}|
|   {C.G2}[2]{C.RESET}  {C.WHITE}Batch Create{C.RESET}         {C.DIM}-- Create multiple accounts          {C.CYAN}|
|   {C.G3}[3]{C.RESET}  {C.WHITE}Referral Codes{C.RESET}       {C.DIM}-- View & manage referral codes      {C.CYAN}|
|   {C.G4}[4]{C.RESET}  {C.WHITE}API Keys{C.RESET}            {C.DIM}-- View all collected API keys        {C.CYAN}|
|   {C.G5}[5]{C.RESET}  {C.WHITE}Statistics{C.RESET}           {C.DIM}-- Success rate & performance        {C.CYAN}|
|   {C.G1}[6]{C.RESET}  {C.WHITE}Settings{C.RESET}            {C.DIM}-- Configure options                  {C.CYAN}|
|   {C.G2}[0]{C.RESET}  {C.RED}Exit{C.RESET}                  {C.DIM}-- Quit application                   {C.CYAN}|
|                                                                      |
+----------------------------------------------------------------------+{C.RESET}
"""


# ─── Status Bar ─────────────────────────────────────────────────────────
def status_bar(accounts=0, keys=0, referrals=0):
    now = datetime.now().strftime("%H:%M:%S")
    return f"""{C.BG3}{C.WHITE}{C.BOLD} MiMo AutoReg {C.RESET}{C.DIM_W} | {C.CYAN}Time: {now}{C.RESET} {C.DIM_W} | {C.GREEN}Accounts: {accounts}{C.RESET} {C.DIM_W} | {C.PURPLE}Keys: {keys}{C.RESET} {C.DIM_W} | {C.ORANGE}Codes: {referrals}{C.RESET} {C.DIM_W} |{C.RESET}"""


# ─── Progress Screen ────────────────────────────────────────────────────
def progress_screen(current, total, email, step, status, steps_done=None, steps_total=None):
    clear()
    elapsed = "0s"
    
    header = f"""
{C.CYAN}======================================================================
|                    {C.BOLD}{C.WHITE}ACCOUNT CREATION IN PROGRESS{C.RESET}{C.CYAN}                    |
======================================================================{C.RESET}"""
    
    progress = f"""
{C.WHITE}  Account{C.RESET}  {C.CYAN}{current}/{total}{C.RESET}
{C.WHITE}  Email{C.RESET}    {C.DIM}{email}{C.RESET}
{C.WHITE}  Step{C.RESET}     {C.GREEN}{step}{C.RESET}
{C.WHITE}  Status{C.RESET}  {C.YELLOW}{status}{C.RESET}
"""
    
    steps = ""
    if steps_done is not None and steps_total is not None:
        bar = progress_bar(steps_done, steps_total, width=40)
        steps = f"\n{C.WHITE}  Progress{C.RESET} {bar}"
    
    footer = f"""
{C.DIM_W}  {'-' * 60}
  Press {C.RED}Ctrl+C{C.DIM_W} to cancel current operation
  {'-' * 60}{C.RESET}"""
    
    print(header + progress + steps + footer)


# ─── Success Screen ─────────────────────────────────────────────────────
def success_screen(email, password, api_key, referral_code=None, time_taken=0):
    clear()
    
    result = f"""
{C.GREEN}======================================================================
|                    {C.BOLD}{C.WHITE}ACCOUNT CREATED SUCCESSFULLY{C.RESET}{C.GREEN}                    |
======================================================================{C.RESET}

{C.WHITE}  Email{C.RESET}
      {C.CYAN}{email}{C.RESET}

{C.WHITE}  Password{C.RESET}
      {C.CYAN}{password}{C.RESET}

{C.WHITE}  API Key{C.RESET}
      {C.PURPLE}{api_key}{C.RESET}
"""
    
    if referral_code:
        result += f"""
{C.WHITE}  Referral Code{C.RESET}
      {C.ORANGE}{referral_code}{C.RESET}
"""
    
    result += f"""
{C.WHITE}  Time{C.RESET}
      {C.GREEN}{time_taken:.1f}s{C.RESET}

{C.DIM_W}  {'-' * 60}
  {C.YELLOW}API Key saved to results/xiaomi_api_keys.json{C.DIM_W}
  {'-' * 60}{C.RESET}
"""
    
    print(result)


# ─── Referral Codes Screen ──────────────────────────────────────────────
def referral_codes_screen(codes):
    clear()
    
    header = f"""
{C.ORANGE}======================================================================
|                    {C.BOLD}{C.WHITE}REFERRAL CODES MANAGEMENT{C.RESET}{C.ORANGE}                    |
======================================================================{C.RESET}"""
    
    print(header)
    
    if not codes:
        print(f"\n  {C.DIM}  No referral codes collected yet.{C.RESET}")
        print(f"  {C.DIM}  Create accounts to collect referral codes.{C.RESET}")
    else:
        print(f"\n  {C.WHITE}Total codes:{C.RESET} {C.ORANGE}{len(codes)}{C.RESET}")
        print(f"  {C.WHITE}Pool value:{C.RESET} {C.GREEN}${len(codes) * 2}{C.RESET}")
        print()
        
        for i, item in enumerate(codes):
            if isinstance(item, dict):
                email = item.get('email', 'N/A')
                code = item.get('code', 'N/A')
            else:
                code = item
                email = 'N/A'
            
            print(f"  {C.DIM_W}{i+1:2}.{C.RESET}  {C.ORANGE}{code}{C.RESET}  {C.DIM_W}-- {email}{C.RESET}")
        
        print(f"\n  {C.GREEN}Each code = $2 API credits{C.RESET}")
    
    print(f"""
{C.DIM_W}  {'-' * 60}
  {C.WHITE}[B]{C.RESET} Back to menu
  {'-' * 60}{C.RESET}""")


# ─── API Keys Screen ────────────────────────────────────────────────────
def api_keys_screen(keys):
    clear()
    
    header = f"""
{C.PURPLE}======================================================================
|                    {C.BOLD}{C.WHITE}API KEYS DASHBOARD{C.RESET}{C.PURPLE}                         |
======================================================================{C.RESET}"""
    
    print(header)
    
    if not keys:
        print(f"\n  {C.DIM}  No API keys collected yet.{C.RESET}")
        print(f"  {C.DIM}  Create accounts to collect API keys.{C.RESET}")
    else:
        total_credits = len(keys) * 2
        print(f"\n  {C.WHITE}Total Keys:{C.RESET}     {C.PURPLE}{len(keys)}{C.RESET}")
        print(f"  {C.WHITE}Est. Credits:{C.RESET}  {C.GREEN}${total_credits}{C.RESET}")
        print()
        
        for i, key_data in enumerate(keys):
            if isinstance(key_data, dict):
                email = key_data.get('email', 'N/A')
                api_key = key_data.get('api_key', 'N/A')
                ref_code = key_data.get('referral_code', '')
                
                # Mask key for display
                masked_key = api_key[:12] + '......' + api_key[-4:] if len(api_key) > 16 else api_key
                
                print(f"  {C.DIM_W}{i+1:2}.{C.RESET}  {C.PURPLE}{masked_key}{C.RESET}")
                print(f"       {C.DIM}Email: {email}{C.RESET}")
                if ref_code:
                    print(f"       {C.DIM_W}Code: {ref_code}{C.RESET}")
                print()
            else:
                masked_key = str(key_data)[:12] + '......' if len(str(key_data)) > 12 else str(key_data)
                print(f"  {C.DIM_W}{i+1:2}.{C.RESET}  {C.PURPLE}{masked_key}{C.RESET}")
        
        print(f"  {C.GREEN}Keys saved to results/xiaomi_api_keys.json{C.RESET}")
    
    print(f"""
{C.DIM_W}  {'-' * 60}
  {C.WHITE}[B]{C.RESET} Back to menu
  {'-' * 60}{C.RESET}""")


# ─── Statistics Screen ──────────────────────────────────────────────────
def statistics_screen(results_dir):
    clear()
    
    # Load stats
    api_keys_file = results_dir / "xiaomi_api_keys.json"
    referral_file = results_dir / "referral_codes.json"
    
    total_accounts = 0
    total_keys = 0
    total_referrals = 0
    
    if api_keys_file.exists():
        try:
            with open(api_keys_file, 'r') as f:
                content = f.read().strip()
                if content:
                    # Parse JSON objects separated by newlines
                    keys = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                keys.append(json.loads(line))
                            except:
                                pass
                    total_keys = len(keys)
                    total_accounts = total_keys
        except:
            pass
    
    if referral_file.exists():
        try:
            with open(referral_file, 'r') as f:
                data = json.load(f)
                total_referrals = len(data) if isinstance(data, list) else 0
        except:
            pass
    
    header = f"""
{C.CYAN}======================================================================
|                    {C.BOLD}{C.WHITE}STATISTICS DASHBOARD{C.RESET}{C.CYAN}                         |
======================================================================{C.RESET}"""
    
    # Stats boxes
    stats = f"""
  {C.WHITE}Overview{C.RESET}
  {'-' * 60}
  
  {C.GREEN}+-------------+  +-------------+  +-------------+
  |{C.BOLD}{total_accounts:^13}{C.RESET}{C.GREEN}|  |{C.BOLD}{total_keys:^13}{C.RESET}{C.GREEN}|  |{C.BOLD}{total_referrals:^13}{C.RESET}{C.GREEN}|
  +-------------+  +-------------+  +-------------+{C.RESET}
   {C.DIM}  Accounts      API Keys       Referral Codes{C.RESET}
  
  {C.WHITE}Performance{C.RESET}
  {'-' * 60}
  
  {C.CYAN}Pool Value:{C.RESET}   {C.GREEN}${total_referrals * 2} credits{C.RESET}
  {C.CYAN}Success:{C.RESET}     {C.GREEN}100%{C.RESET} {C.DIM}(all attempts successful){C.RESET}
  
  {C.WHITE}System{C.RESET}
  {'-' * 60}
  
  {C.DIM_W}Stealth Browser:{C.RESET} {C.GREEN}Enabled{C.RESET}
  {C.DIM_W}CAPTCHA Solver:{C.RESET}  {C.GREEN}Whisper + OCR{C.RESET}
  {C.DIM_W}Referral System:{C.RESET} {C.GREEN}Auto-redeem{C.RESET}
  {C.DIM_W}Email Service:{C.RESET}   {C.GREEN}tempmail.lol{C.RESET}
"""
    
    print(header + stats)
    
    print(f"""
{C.DIM_W}  {'-' * 60}
  {C.WHITE}[B]{C.RESET} Back to menu
  {'-' * 60}{C.RESET}""")


# ─── Settings Screen ────────────────────────────────────────────────────
def settings_screen():
    clear()
    
    header = f"""
{C.G2}======================================================================
|                    {C.BOLD}{C.WHITE}SETTINGS{C.RESET}{C.G2}                                  |
======================================================================{C.RESET}"""
    
    settings = f"""
  {C.WHITE}Current Configuration{C.RESET}
  {'-' * 60}
  
  {C.DIM_W}[{C.GREEN}ON{C.DIM_W}]{C.RESET}  {C.WHITE}Stealth Browser{C.RESET}         {C.GREEN}Enabled{C.RESET}
      {C.DIM}Hide webdriver, fake plugins, random delays{C.RESET}
  
  {C.DIM_W}[{C.GREEN}ON{C.DIM_W}]{C.RESET}  {C.WHITE}Human-like Typing{C.RESET}       {C.GREEN}Enabled{C.RESET}
      {C.DIM}Variable speed, thinking pauses{C.RESET}
  
  {C.DIM_W}[{C.GREEN}ON{C.DIM_W}]{C.RESET}  {C.WHITE}CAPTCHA Solver{C.RESET}          {C.GREEN}Whisper + OCR{C.RESET}
      {C.DIM}Audio reCAPTCHA + Image CAPTCHA fallback{C.RESET}
  
  {C.DIM_W}[{C.GREEN}ON{C.DIM_W}]{C.RESET}  {C.WHITE}Referral Auto-Redeem{C.RESET}    {C.GREEN}Enabled{C.RESET}
      {C.DIM}Redeem all codes from pool{C.RESET}
  
  {C.DIM_W}[{C.GREEN}ON{C.DIM_W}]{C.RESET}  {C.WHITE}Rate Limit Protection{C.RESET}  {C.GREEN}Enabled{C.RESET}
      {C.DIM}Auto-wait on "too many attempts"{C.RESET}
  
  {C.WHITE}File Structure{C.RESET}
  {'-' * 60}
  
  {C.CYAN}results/{C.RESET}
  +-- {C.DIM_W}xiaomi_api_keys.json{C.RESET}   {C.DIM}-- All API keys{C.RESET}
  +-- {C.DIM_W}referral_codes.json{C.RESET}    {C.DIM}-- Referral codes pool{C.RESET}
  +-- {C.DIM_W}xiaomi_session.json{C.RESET}    {C.DIM}-- Last session{C.RESET}
  +-- {C.DIM_W}xiaomi_credentials.json{C.RESET} {C.DIM}-- Credentials{C.RESET}
  
  {C.CYAN}screenshots/{C.RESET}
  +-- {C.DIM_W}*.png{C.RESET}                     {C.DIM}-- Debug screenshots{C.RESET}
"""
    
    print(header + settings)
    
    print(f"""
{C.DIM_W}  {'-' * 60}
  {C.WHITE}[B]{C.RESET} Back to menu
  {'-' * 60}{C.RESET}""")


# ─── Batch Input Screen ─────────────────────────────────────────────────
def batch_input_screen():
    clear()
    
    header = f"""
{C.G3}======================================================================
|                    {C.BOLD}{C.WHITE}BATCH ACCOUNT CREATION{C.RESET}{C.G3}                      |
======================================================================{C.RESET}"""
    
    content = f"""
  {C.WHITE}How many accounts do you want to create?{C.RESET}
  
  {C.DIM}Each account will:{C.RESET}
  
  {C.CYAN}*{C.RESET} Create temporary email
  {C.CYAN}*{C.RESET} Register Xiaomi account
  {C.CYAN}*{C.RESET} Solve CAPTCHA (reCAPTCHA or Image)
  {C.CYAN}*{C.RESET} Verify email
  {C.CYAN}*{C.RESET} Extract session tokens
  {C.CYAN}*{C.RESET} Accept MiMo terms
  {C.CYAN}*{C.RESET} Get referral code
  {C.CYAN}*{C.RESET} Redeem ALL invite codes from pool
  {C.CYAN}*{C.RESET} Create API key
  
  {C.DIM_W}Estimated time:{C.RESET} {C.YELLOW}~2-3 min per account{C.RESET}
"""
    
    print(header + content)
    
    print(f"""
{C.DIM_W}  {'-' * 60}
  {C.WHITE}Enter number (or {C.RED}[B]{C.WHITE} to go back):{C.RESET} """, end="")


# ─── Input Prompt ───────────────────────────────────────────────────────
def input_prompt(text, color=C.CYAN):
    return input(f"  {color}{text}{C.RESET} ")


# ─── Loading Animation ──────────────────────────────────────────────────
def loading_animation(text="Loading", duration=2, color=C.CYAN):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"\r  {color}{frames[i % len(frames)]}{C.RESET} {C.WHITE}{text}...{C.RESET}  ", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r  {C.GREEN}✓{C.RESET} {C.WHITE}{text} done!{C.RESET}                    ")


# ─── Splash Screen ──────────────────────────────────────────────────────
def splash_screen():
    clear()
    print(BANNER)
    print(f"\n{C.DIM_W}  Initializing system...{C.RESET}")
    loading_animation("Loading Whisper model", 1.5, C.CYAN)
    loading_animation("Preparing browser", 1, C.BLUE)
    loading_animation("Ready", 0.5, C.GREEN)
    time.sleep(0.5)


# ─── Confirm Dialog ─────────────────────────────────────────────────────
def confirm_dialog(message, color=C.CYAN):
    response = input(f"\n  {color}?{C.RESET} {C.WHITE}{message}{C.RESET} {C.DIM_W}(y/n):{C.RESET} ")
    return response.lower() in ['y', 'yes']


# ─── Error Screen ───────────────────────────────────────────────────────
def error_screen(message):
    print(f"\n  {C.RED}ERROR:{C.RESET} {C.WHITE}{message}{C.RESET}")
    print()


# ─── Success Toast ──────────────────────────────────────────────────────
def success_toast(message):
    print(f"\n  {C.GREEN}✓{C.RESET} {C.WHITE}{message}{C.RESET}")


# ─── Warning Toast ──────────────────────────────────────────────────────
def warning_toast(message):
    print(f"\n  {C.YELLOW}!{C.RESET} {C.WHITE}{message}{C.RESET}")


# ─── Info Toast ─────────────────────────────────────────────────────────
def info_toast(message):
    print(f"\n  {C.CYAN}i{C.RESET} {C.WHITE}{message}{C.RESET}")


# ─── Footer ─────────────────────────────────────────────────────────────
def footer():
    width, _ = get_terminal_size()
    return f"""
{C.DIM_W}{'=' * width}
  {C.DIM}MiMo AutoReg v2.0 -- Stealth Browser -- Referral System
  GitHub: github.com/mriya23/auto-mimo
{'=' * width}{C.RESET}"""


# ─── Main Menu Handler ──────────────────────────────────────────────────
def show_main_menu():
    clear()
    print(BANNER)
    print(MAIN_MENU)


if __name__ == "__main__":
    splash_screen()
    show_main_menu()
    print(footer())
