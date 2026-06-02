/* SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note */
#ifndef __ASM_WASM32_SWAB_H
#define __ASM_WASM32_SWAB_H

#include <linux/types.h>


static __inline__  __u32 __arch_swab32(__u32 val)
{
	return __builtin_bswap32(val);
}
#define __arch_swab32 __arch_swab32

static __inline__  __u64 __arch_swab64(__u64 val)
{
	return __builtin_bswap64(val);
}
#define __arch_swab64 __arch_swab64

#endif /* __ASM_WASM32_SWAB_H */
