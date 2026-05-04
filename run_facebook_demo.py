import os
import sys
from app.services.nlp_service import NLPService
from app.services.vision_service import VisionService
from app.services.executor_service import ExecutorService
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nlp_service import NLPService
# 1. Start the Brains
print("🧠 Initializing AI Agent for Facebook...")
nlp = NLPService()
vision = VisionService()
executor = ExecutorService(nlp, vision)

# 2. Scenario Gherkin (Twil & Realistic)
# Houni l-agent bech y-handle-i el cookies, el login, w ba3d y-thabbet f'el erreur
scenario = [
    "Given I navigate to 'https://www.facebook.com'",
    "And I click the 'Allow all cookies' button", # Fallback Vision mte3ek bech yal9ah houni
    "When I type 'nour.pfe.test@gmail.com' into the email field",
    "And I type 'PFE2026_DataIA' into the password field",
    "And I click the login button",
    "Then I should see 'The email address you entered isn't connected to an account'"
]

print(f"🚀 Execution of Facebook Pipeline started ({len(scenario)} steps)...")

for step in scenario:
    print(f"\n--- Processing: {step} ---")
    result = executor.execute_gherkin_step(step)
    
    if result['success']:
        print(f"✅ Step Passed! Report: {result['report_path']}")
    else:
        # Houni ken l-ID mta3 FB t-badel, el YOLO bech y-isauvi el danya
        print(f"⚠️ Plan A failed, but Agent is still trying with Vision...")

print("\n🎯 Pipeline Finished. Check reports/html/ for the full proof!")