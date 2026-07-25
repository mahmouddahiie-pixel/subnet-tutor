# Finger Counting Method for Subnetting

The finger counting method helps you quickly find how many subnets you can create by borrowing host bits.

## How It Works

1. Start with one network (e.g., 192.168.1.0/24).
2. Raise one finger for each bit you borrow from the host portion.
3. Count by powers of two: 2, 4, 8, 16, 32, 64, 128, 256.
4. The number at your last raised finger equals the number of subnets: subnets = 2^borrowed_bits.

## Finger Table (Class C /24 starting point)

| Fingers | Subnets | Block Size | Mask (4th octet) | New Prefix |
|---------|---------|------------|------------------|------------|
| 1       | 2       | 128        | 128              | /25        |
| 2       | 4       | 64         | 192              | /26        |
| 3       | 8       | 32         | 224              | /27        |
| 4       | 16      | 16         | 240              | /28        |
| 5       | 32      | 8          | 248              | /29        |
| 6       | 64      | 4          | 252              | /30        |
| 7       | 128     | 2          | 254              | /31        |
| 8       | 256     | 1          | 255              | /32        |

## Key Formulas

- Subnets created = 2^borrowed_bits
- Usable hosts per subnet = 2^host_bits - 2 (subtract network and broadcast)
- Block size = 2^host_bits_in_the_subnet_octet
- New prefix = original prefix + borrowed_bits

## Worked Example: Need at least 6 subnets from 192.168.1.0/24

1. Raise fingers: 2 (1 finger), 4 (2 fingers), 8 (3 fingers).
2. 8 >= 6, so borrow 3 bits.
3. New prefix: /24 + 3 = /27
4. Block size: 32 (from finger 3)
5. Subnet mask: 255.255.255.224
6. Subnets: 192.168.1.0/27, 192.168.1.32/27, 192.168.1.64/27, ...

## Worked Example: Need at least 25 hosts per subnet from 192.168.5.0/24

1. Find host bits: smallest n where 2^n - 2 >= 25 → 2^5 - 2 = 30 hosts
2. Need 5 host bits in last octet → prefix = 32 - 5 = /27
3. Borrowed bits = 27 - 24 = 3
4. Subnets = 2^3 = 8 subnets
5. Block size = 32

## Paper Fold Metaphor

Imagine a paper strip representing your network. Each fold splits it in half:
- 1 fold → 2 pieces (2 subnets)
- 2 folds → 4 pieces (4 subnets)
- 3 folds → 8 pieces (8 subnets)

Each fold borrows one more bit from the host side.
