from ui import compat, consent_dialog


def test_consent_dialog_uses_bootstyle_compatible_widgets():
    assert consent_dialog.Button is compat.Button
    assert consent_dialog.Checkbutton is compat.Checkbutton
