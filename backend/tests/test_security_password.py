from app.core.security import get_password_hash, verify_password

def test_normal_password_hashing():
    pwd = "StandardPassword123!"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False

def test_long_password_hashing_without_truncation_collision():
    # 100 character password
    long_pwd_1 = "A" * 72 + "ExtraString1"
    long_pwd_2 = "A" * 72 + "ExtraString2"

    hash_1 = get_password_hash(long_pwd_1)
    hash_2 = get_password_hash(long_pwd_2)

    # Verify both verify correctly
    assert verify_password(long_pwd_1, hash_1) is True
    assert verify_password(long_pwd_2, hash_2) is True

    # Verify that truncation collision DOES NOT occur
    assert verify_password(long_pwd_2, hash_1) is False
    assert verify_password(long_pwd_1, hash_2) is False
