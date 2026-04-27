from app.utils.text_similarity import TextSimilarity


def test_multilingual_email_mobile_match():
    target = "e-mail ou numero de mobile"
    detected = "Email or mobile number"

    assert TextSimilarity.is_match(target, detected) is True


def test_password_translation_match():
    target = "mot de passe"
    detected = "Password"

    assert TextSimilarity.is_match(target, detected) is True


def test_unrelated_text_does_not_match():
    target = "login button"
    detected = "forgot password"

    assert TextSimilarity.is_match(target, detected) is False
