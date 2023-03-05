def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    print(bin(sign_bit), bin(value), value & (sign_bit - 1), bin(value & sign_bit))
    res = (value & (sign_bit - 1)) - (value & sign_bit)
    # ？
    if res >= 2**31:
        res -= 2**32
    return bin(res)

print(sign_extend(0xFF, 8))