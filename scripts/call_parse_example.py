import json
import urllib.request

url = "http://127.0.0.1:8000/api/ia/parse-gherkin"
gherkin = '''Feature: Login
  Scenario: Valid login
    Given I navigate to "https://example.com"
    When I click the "login" button
    Then I should see "success"
'''

data = {"gherkin_text": gherkin}
req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(json.dumps(json.loads(resp.read().decode()), indent=2, ensure_ascii=False))
