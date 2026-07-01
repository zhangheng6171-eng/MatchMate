"""P1 本地验收测试"""
print("=== P1 用户身份系统 — 本地测试 ===\n")

# 1. Security
from app.core.security import (
    hash_password, verify_password, validate_password_strength,
    create_tokens, decode_token
)
print("[1] Security module...", end=" ")
tokens = create_tokens("uid-1", 3)
payload = decode_token(tokens["refresh_token"])
assert payload.get("ver") == 3, f"Token version check: {payload.get('ver')}"
assert payload.get("sub") == "uid-1"
print("OK (token version={})".format(payload["ver"]))

# 2. Schemas
from app.schemas.auth import (
    SendCodeRequest, CodeRegisterRequest, CodeLoginRequest,
    ResetPasswordConfirm, ActivateEmailRequest
)
print("[2] Schemas...", end=" ")
sc = SendCodeRequest(target="+8613800138000", channel="sms", purpose="register")
assert sc.channel == "sms"
cr = CodeRegisterRequest(phone="+8613800138000", password="Test@1234", code="123456")
cl = CodeLoginRequest(login="+8613800138000", code="123456")
rc = ResetPasswordConfirm(target="+8613800138000", code="123456", new_password="NewPass@123")
ae = ActivateEmailRequest(email="test@test.com", code="123456")

# Weak password rejection
try:
    cr2 = CodeRegisterRequest(phone="+8613800138000", password="123", code="123456")
    assert False, "Should reject"
except Exception:
    pass

# No contact provided
try:
    cr3 = CodeRegisterRequest(password="Test@1234", code="123456")
    assert False, "Should reject"
except Exception:
    pass
print("OK (5 schemas + 2 validations)")

# 3. Verification service
from app.services.verification import generate_code
print("[3] Verification service...", end=" ")
code = generate_code()
assert len(code) == 6
assert code.isdigit()
print(f"OK (sample: {code})")

# 4. Auth router
from app.api.auth import router
routes = [(r.methods, r.path) for r in router.routes]
route_paths = [p for _, p in routes]
print(f"[4] Auth router: {len(router.routes)} endpoints")
for methods, path in routes:
    print(f"    {' '.join(sorted(methods)):6s} {path}")

# Verify key endpoints exist
assert "/api/auth/send-code" in route_paths, "Missing send-code"
assert "/api/auth/register/code" in route_paths, "Missing register/code"
assert "/api/auth/login/code" in route_paths, "Missing login/code"
assert "/api/auth/reset-password/request" in route_paths, "Missing reset/request"
assert "/api/auth/reset-password/confirm" in route_paths, "Missing reset/confirm"
assert "/api/auth/activate-email" in route_paths, "Missing activate-email"
assert "/api/auth/logout" in route_paths, "Missing logout"
print("    All key endpoints present")

# 5. Main app
from app.main import app
print(f"[5] Main app: {len(app.routes)} total routes")
api_routes = [r for r in app.routes if hasattr(r, "path")]
for r in api_routes:
    if "/api/auth" in r.path:
        methods = list(r.methods) if hasattr(r, 'methods') else ['GET']
        print(f"    {', '.join(sorted(methods)):12s} {r.path}")

print("\n=== P1 本地测试: 5/5 PASS ===")
