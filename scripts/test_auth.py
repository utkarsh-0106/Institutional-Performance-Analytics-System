"""Verify authentication returns dicts and accepts demo credentials."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auth.auth_service import authenticate_user


def main():
    tests = [
        ("admin", "admin123", True),
        ("institution_user", "user123", True),
        ("admin", "wrong", False),
    ]
    for username, password, should_pass in tests:
        result = authenticate_user(username, password)
        ok = (result is not None) == should_pass
        assert ok, f"Failed for {username}/{password}: got {result}"
        if result:
            assert isinstance(result, dict), "Must return dict"
            assert "id" in result and "username" in result and "role" in result
            assert not hasattr(result, "_sa_instance_state"), "Must not be ORM"
            print(f"PASS {username}: id={result['id']} role={result['role']}")
        else:
            print(f"PASS {username}: rejected as expected")
    print("All auth tests passed.")


if __name__ == "__main__":
    main()
