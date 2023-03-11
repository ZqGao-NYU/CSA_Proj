def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    res = (value & (sign_bit - 1)) - (value & sign_bit)
    # ？
    # if res >= 2**31:
    #     res -= 2**32
    return res

print(sign_extend(3, 2))

# A = [x for x in range(-32, 0)]
# print(A)
# print(A[-20:-12])

B = [x for x in range(31, -1, -1)]
print(B)
print(B[-12:-8])