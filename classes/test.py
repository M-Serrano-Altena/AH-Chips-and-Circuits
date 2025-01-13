import itertools

offsets = itertools.product([-1, 0, 1], repeat=3)

print(list(offsets))

l = [3, 2, 1]
print(sorted(l)[0])