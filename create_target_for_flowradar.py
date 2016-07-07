#!/usr/bin/env python2

from __future__ import print_function

import os
from string import Template


mother_function_str = """

/*
 * The following murmur3_32 code is copied from wikipedia: https://en.wikipedia.org/wiki/MurmurHash
 * as well as https://github.com/USC-NSL/p4c-behavioral/blob/master/p4c_bm/templates/src/checksums_algos.h
 */

#define ROT32(x, y) ((x << y) | (x >> (32 - y))) // avoid effort
static inline uint32_t murmur3_32(const char *key, uint32_t len, uint32_t seed) {
	static const uint32_t c1 = 0xcc9e2d51;
	static const uint32_t c2 = 0x1b873593;
	static const uint32_t r1 = 15;
	static const uint32_t r2 = 13;
	static const uint32_t m = 5;
	static const uint32_t n = 0xe6546b64;

	uint32_t hash = seed;

	const int nblocks = len / 4;
	const uint32_t *blocks = (const uint32_t *) key;
	int i;
	uint32_t k;
	for (i = 0; i < nblocks; i++) {
		k = blocks[i];
		k *= c1;
		k = ROT32(k, r1);
		k *= c2;

		hash ^= k;
		hash = ROT32(hash, r2) * m + n;
	}

	const uint8_t *tail = (const uint8_t *) (key + nblocks * 4);
	uint32_t k1 = 0;

	switch (len & 3) {
		case 3:
			k1 ^= tail[2] << 16;
		case 2:
			k1 ^= tail[1] << 8;
		case 1:
			k1 ^= tail[0];

			k1 *= c1;
			k1 = ROT32(k1, r1);
			k1 *= c2;
			hash ^= k1;
	}

	hash ^= len;
	hash ^= (hash >> 16);
	hash *= 0x85ebca6b;
	hash ^= (hash >> 13);
	hash *= 0xc2b2ae35;
	hash ^= (hash >> 16);

	return hash;
}

"""


hash_func_definition_template= Template("""
struct $hash_func_name {
  uint32_t operator()(const char *buf, size_t s) const {
    return murmur3_32(buf, s, $index);
  }
};
""")


hash_func_registration_template = Template("REGISTER_HASH($hash_func_name);\n")


def gen_code(n=22, hash_func_prefix='my_hash'):
    hash_func_definitions = ""
    hash_func_registrations = ""
    for i in range(1, n+1):
        hash_func_name = hash_func_prefix+str(i)
        hash_func_definitions += hash_func_definition_template.substitute(hash_func_name=hash_func_name, index=i)
        hash_func_registrations += hash_func_registration_template.substitute(hash_func_name=hash_func_name)
    return hash_func_definitions, hash_func_registrations


def gen_flowradar_target(target_name='flow_radar', bmv2_path='~/bmv2', base_target_name='simple_switch'):
    home_path = os.path.expanduser(bmv2_path)
    targets_path = os.path.join(home_path, 'targets')
    os.chdir(targets_path)
    os.system('rm -rf ' + target_name)
    os.system("cp -r {0} {1}".format(base_target_name, target_name))
    os.chdir(target_name)

    cpp_file = base_target_name + '.cpp'

    with open(cpp_file) as f:
        text = f.read()

    if mother_function_str in text:
        return

    hash_func_definitions, hash_func_registrations = gen_code()
    #print(hash_func_definitions)
    #print(hash_func_registrations)

    original_str = 'namespace {'

    wanted_str = '{0}\n{1}\n{2}'.format(mother_function_str, original_str, hash_func_definitions)
    text = text.replace(original_str, wanted_str)

    original_str = 'extern int import_primitives();'
    wanted_str = '{0}\n{1}'.format(hash_func_registrations, original_str)
    text = text.replace(original_str, wanted_str)

    with open(cpp_file, "w") as f:
        f.write(text)

    os.system('make clean')
    os.system('make')

    print('\nDone!')


def main():
    gen_flowradar_target()


if __name__ == '__main__':
    main()
