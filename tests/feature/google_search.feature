Feature: Google search pipeline smoke
  As a tester
  I want the pipeline to search Google
  So I can validate browser execution and reporting

  Scenario: Search for OpenAI on Google
    Given I navigate to "https://www.google.com/search?q=OpenAI"
    Then I should see "OpenAI"
