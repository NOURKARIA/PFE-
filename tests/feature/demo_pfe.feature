Feature: Demo PFE end-to-end scenario
  As a tester
  I want the pipeline to execute a full user scenario
  So I can get a report of what happened

  Background:
    Given the browser is ready

  Scenario: Submit login form on Facebook
    Given I navigate to "https://www.facebook.com"
    When I click the "Allow all cookies" button
    And I fill the "email" field with "nour.karia@h"
    And I fill the "pass" field with "tourbillon 1234"
    And I click the "login" button
    Then I should see "isn't connected to an account"
