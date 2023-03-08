def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    res = (value & (sign_bit - 1)) - (value & sign_bit)
    # ？
    if res >= 2**31:
        res -= 2**32
    return bin(res)

print(sign_extend(3, 3))