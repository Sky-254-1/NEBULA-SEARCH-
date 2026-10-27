"""Guards against weak default credentials in Kubernetes manifests."""

from pathlib import Path

KUBERNETES_DIR = Path(__file__).resolve().parents[2] / "kubernetes"
SECRETS_MANIFEST = KUBERNETES_DIR / "configs" / "secrets.yaml"

# Base64 of well-known weak placeholders that must never ship in a manifest.
WEAK_BASE64_VALUES = {
    "YWRtaW4=": "admin",
    "bWluaW9hZG1pbg==": "minioadmin",
    "bmlibHVh": "nebula",
    "LS0tLS1CRUdJTi": "placeholder PEM",
}


def test_secrets_manifest_ships_no_credentials():
    text = SECRETS_MANIFEST.read_text(encoding="utf-8")

    for token, label in WEAK_BASE64_VALUES.items():
        assert token not in text, f"weak placeholder {label!r} found in {SECRETS_MANIFEST}"

    # Both Secret objects must be declared with an empty data map (fail closed).
    assert text.count("data: {}") >= 2
    # A placeholder TLS cert must not be shipped.
    assert "tls.crt" not in text and "tls.key" not in text


def test_kubernetes_manifests_have_no_weak_default_passwords():
    offenders = []
    for path in KUBERNETES_DIR.rglob("*.yaml"):
        if path.name == "secrets.example.yaml":
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for weak in ("password: admin", "minioadmin", "password: nebula", "password: password"):
            if weak in lowered:
                offenders.append(f"{path.relative_to(KUBERNETES_DIR)}: {weak}")

    assert not offenders, "weak credentials in manifests: " + ", ".join(offenders)
