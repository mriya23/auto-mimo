"""
MiMo AutoReg - Launcher with UI
"""
import os
import sys
import json
import time
from pathlib import Path

# Force UTF-8 for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import *
from main import XiaomiAuto, TempMailAPI, gen_password, log, XIAOMI_URL, MAIL_API

RESULTS_DIR = Path("results")

def load_json_file(filepath):
    """Load JSON file with error handling"""
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            # Handle newline-separated JSON objects
            items = []
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except:
                        pass
            return items
    except:
        return []

def load_referral_codes():
    """Load referral codes from JSON file"""
    filepath = RESULTS_DIR / "referral_codes.json"
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return []

def get_stats():
    """Get current statistics"""
    api_keys = load_json_file(RESULTS_DIR / "xiaomi_api_keys.json")
    referrals = load_referral_codes()
    return {
        'accounts': len(api_keys),
        'keys': len(api_keys),
        'referrals': len(referrals)
    }

def handle_create_account():
    """Handle single account creation"""
    clear()
    print(f"""
{C.CYAN}+====================================================================+
|                    {C.BOLD}{C.WHITE}CREATE ACCOUNT{C.RESET}{C.CYAN}                            |
+====================================================================+{C.RESET}
""")
    
    # Load existing referral codes
    referral_codes = load_referral_codes()
    referral_code = None
    
    if referral_codes:
        # Use a random code from pool
        import random
        valid_codes = [c for c in referral_codes if isinstance(c, dict) and 'code' in c]
        if valid_codes:
            referral_code = random.choice(valid_codes)['code']
            info_toast(f"Using referral code: {C.ORANGE}{referral_code}{C.RESET}")
    
    # Confirm
    print(f"\n  {C.WHITE}Ready to create a new account!{C.RESET}")
    if not confirm_dialog("Start account creation?"):
        return
    
    try:
        # Initialize components
        print(f"\n  {C.DIM_W}Initializing...{C.RESET}")
        temp_mail = TempMailAPI()
        auto = XiaomiAuto()
        auto.setup_browser(with_extension=False)
        
        # Create email
        print(f"  {C.CYAN}->{C.RESET} Creating temporary email...")
        temp_email = temp_mail.create_account()
        if not temp_email:
            error_screen("Failed to create temp email")
            return
        print(f"  {C.GREEN}V{C.RESET} Email: {C.CYAN}{temp_email}{C.RESET}")
        
        # Set email and password
        auto.temp_email = temp_email
        auto.password = gen_password()
        
        # Fill form
        print(f"  {C.CYAN}->{C.RESET} Filling registration form...")
        auto.fill_form(referral_code)
        
        # Click Next
        print(f"  {C.CYAN}->{C.RESET} Submitting form...")
        if not auto.click_next():
            error_screen("Failed to click Next")
            return
        
        # Solve CAPTCHA
        print(f"  {C.CYAN}->{C.RESET} Solving CAPTCHA...")
        if not auto.solve_recaptcha_audio(None):
            error_screen("CAPTCHA failed")
            return
        
        # Submit
        print(f"  {C.CYAN}->{C.RESET} Final submission...")
        if not auto.submit_final():
            error_screen("Submission failed")
            return
        
        # Wait for email
        print(f"  {C.CYAN}->{C.RESET} Waiting for verification email...")
        message = temp_mail.wait_for_message("xiaomi", timeout=60)
        if not message:
            error_screen("Verification code not received")
            return
        
        # Extract code from message
        code = temp_mail.extract_verification_code(message)
        if not code:
            error_screen("Could not extract verification code")
            return
        
        # Enter code
        print(f"  {C.CYAN}->{C.RESET} Entering verification code: {code}")
        if not auto.enter_code(code):
            error_screen("Failed to enter verification code")
            return
        
        # Extract session
        print(f"  {C.CYAN}->{C.RESET} Extracting session...")
        session = auto.extract_session()
        
        # Accept terms
        print(f"  {C.CYAN}->{C.RESET} Accepting terms...")
        auto.accept_terms()
        
        # Get referral code
        print(f"  {C.CYAN}->{C.RESET} Getting referral code...")
        new_referral = auto.get_referral_code()
        if new_referral:
            auto.save_referral_code(temp_email, new_referral)
            print(f"  {C.GREEN}V{C.RESET} New referral code: {C.ORANGE}{new_referral}{C.RESET}")
        
        # Redeem invite codes
        print(f"  {C.CYAN}->{C.RESET} Redeeming invite codes...")
        all_codes = load_referral_codes()
        redeemed = auto.use_invite_codes_batch(all_codes, new_referral)
        print(f"  {C.GREEN}V{C.RESET} Redeemed {redeemed} codes")
        
        # Create API key
        print(f"  {C.CYAN}->{C.RESET} Creating API key...")
        api_key = auto.create_api_key()
        
        if api_key:
            # Save result
            result = {
                "email": temp_email,
                "password": auto.password,
                "api_key": api_key,
                "referral_code": new_referral
            }
            
            # Append to JSON file
            with open(RESULTS_DIR / "xiaomi_api_keys.json", "a") as f:
                json.dump(result, f, indent=2)
                f.write("\n")
            
            # Show success
            success_screen(
                temp_email,
                auto.password,
                api_key,
                new_referral
            )
        else:
            error_screen("Failed to create API key")
        
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}! Operation cancelled{C.RESET}")
    except Exception as e:
        import traceback
        error_screen(str(e))
        traceback.print_exc()
    finally:
        try:
            auto.driver.quit()
        except:
            pass

def handle_batch_create():
    """Handle batch account creation"""
    clear()
    batch_input_screen()
    
    try:
        user_input = input()
        if user_input.lower() == 'b':
            return
        
        num_accounts = int(user_input)
        if num_accounts <= 0:
            error_screen("Invalid number")
            return
        
        print(f"\n  {C.WHITE}Creating {num_accounts} accounts...{C.RESET}\n")
        
        # Import the batch function from main
        from main import run
        
        # Run batch
        run(num_accounts)
        
        success_toast(f"Batch complete! Created {num_accounts} accounts")
        
    except ValueError:
        error_screen("Invalid input")
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}⚠ Batch cancelled{C.RESET}")

def handle_referral_codes():
    """Show referral codes"""
    codes = load_referral_codes()
    referral_codes_screen(codes)
    input(f"\n  {C.DIM_W}Press Enter to continue...{C.RESET}")

def handle_api_keys():
    """Show API keys"""
    keys = load_json_file(RESULTS_DIR / "xiaomi_api_keys.json")
    api_keys_screen(keys)
    input(f"\n  {C.DIM_W}Press Enter to continue...{C.RESET}")

def handle_statistics():
    """Show statistics"""
    statistics_screen(RESULTS_DIR)
    input(f"\n  {C.DIM_W}Press Enter to continue...{C.RESET}")

def handle_settings():
    """Show settings"""
    settings_screen()
    input(f"\n  {C.DIM_W}Press Enter to continue...{C.RESET}")

def main():
    """Main entry point"""
    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Show splash
    splash_screen()
    
    while True:
        try:
            # Show menu
            show_main_menu()
            
            # Get choice
            choice = input(f"\n  {C.CYAN}Select option{C.RESET} {C.DIM_W}(0-6):{C.RESET} ")
            
            if choice == '1':
                handle_create_account()
            elif choice == '2':
                handle_batch_create()
            elif choice == '3':
                handle_referral_codes()
            elif choice == '4':
                handle_api_keys()
            elif choice == '5':
                handle_statistics()
            elif choice == '6':
                handle_settings()
            elif choice == '0':
                clear()
                print(f"\n{C.GREEN}  ✓ Goodbye!{C.RESET}\n")
                break
            else:
                error_screen("Invalid option")
                time.sleep(1)
                
        except KeyboardInterrupt:
            clear()
            print(f"\n{C.GREEN}  ✓ Goodbye!{C.RESET}\n")
            break
        except Exception as e:
            error_screen(str(e))
            time.sleep(2)

if __name__ == "__main__":
    main()
