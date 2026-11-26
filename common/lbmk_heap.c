//Heap use for lean-benchmark (LBMK_init_heap_usage, LBMK_get_heap_usage), the same on every board and on the generic
//targets: how much more the code under test had allocated at its worst moment than when the count was reset,
//counted on the sizes requested from malloc, calloc and realloc. It does not depend on the allocator (newlib,
//newlib-nano, pico-sdk) nor on the order of the requests. lean-bsp's bsp_heap_usage (contract 1.4) follows this file.
//
//Definition:
//- live: the sum of the sizes requested for the blocks recorded and not freed yet, all the blocks since the start of
//  the firmware, not only those since the reset.
//- LBMK_init_heap_usage(), the reset, takes live as the baseline; it does not zero live.
//- LBMK_get_heap_usage() is the most live has been since the reset, minus the baseline: never negative. A block
//  allocated before the reset and freed after it lowers live, possibly below the baseline, so allocating that much
//  again does not raise the figure.
//- malloc(n) adds n, calloc(count, n) adds count*n, when they return a block, malloc(0) included (a block of size 0).
//  A failed allocation adds nothing; count*n cannot overflow when calloc succeeds, as C requires calloc to fail then.
//- realloc(p, n) that returns a block replaces the size of p by n (live -= size of p, live += n); the moment both
//  blocks exist during a copy is not counted. A failed realloc(p, n) with n > 0 leaves p as it was. realloc(NULL, n)
//  is malloc(n). realloc(p, 0) that returns NULL freed p (newlib, glibc); if it returns a block, that block counts as a
//  block of size 0.
//- free(NULL) changes nothing, nor does free(p) of a block that was never recorded (allocated before the firmware
//  linked these wrappers, or while the table was full).
//- Only these four functions are counted, under these names: memalign, aligned_alloc and the entry points the C
//  library uses for itself (newlib's _malloc_r for its stdio buffers, for instance) are not.
//- The table of live blocks has LBMK_HEAP_MAX_BLOCKS entries, so that free knows the size it gives back and every
//  call takes a time bounded by that number. When it is full, the allocation still succeeds: the block is returned
//  but never recorded, and LBMK_get_heap_usage() returns UINT64_MAX, the figure being unknown, until the next reset.
//- No lock, and interrupts are left as they are: nothing may allocate or free from an interrupt handler or from
//  another core while the code under test runs.
//
//Linking: a firmware compiles this file, links with
//    -Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc,--wrap=free
//and defines no LBMK_*heap* function of its own. The generic targets (CMakeLists.txt) also link with
//    -Wl,--undefined=lbmk_heap_allocated,--undefined=lbmk_heap_reallocated,--undefined=lbmk_heap_freed
//so that the count and its table are in every build, the STUB included: the footprint of a library (its firmware
//minus the STUB's, report_footprint.py) leaves them out. It counts the C library's allocation functions the library
//calls, as before, and the wrappers of those functions below, which are only a few instructions each.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifndef LBMK_HEAP_MAX_BLOCKS
#define LBMK_HEAP_MAX_BLOCKS 256
#endif

void *__real_malloc(size_t size);
void *__real_calloc(size_t count, size_t size);
void *__real_realloc(void *mem, size_t size);
void __real_free(void *mem);

static void *block_ptr[LBMK_HEAP_MAX_BLOCKS];
static size_t block_size[LBMK_HEAP_MAX_BLOCKS];
static unsigned int nblocks;
static size_t live;     //bytes recorded and not freed yet
static size_t baseline; //live at the last reset
static size_t peak;     //the most live since then
static bool overflow;   //a block could not be recorded since then

static void add_block(void *mem, size_t size){
    if(!mem) return;
    if(nblocks == LBMK_HEAP_MAX_BLOCKS){
        overflow = true;
        return;
    }
    block_ptr[nblocks] = mem;
    block_size[nblocks] = size;
    nblocks++;
    live += size;
    if(live > peak) peak = live;
}

static void remove_block(void *mem){
    if(!mem) return;
    for(unsigned int i = 0; i < nblocks; i++){
        if(block_ptr[i] == mem){
            live -= block_size[i];
            nblocks--;
            block_ptr[i] = block_ptr[nblocks];
            block_size[i] = block_size[nblocks];
            return;
        }
    }
}

void LBMK_init_heap_usage(){
    baseline = live;
    peak = live;
    overflow = false;
}

uint64_t LBMK_get_heap_usage(){
    if(overflow) return UINT64_MAX;
    return peak - baseline;
}

//The count, called by the wrappers. noipa: one copy of each, the same in every build, that link time optimization
//neither inlines into the wrappers nor specializes for the library's calls.
__attribute__((noipa)) void *lbmk_heap_allocated(void *mem, size_t size){
    add_block(mem, size);
    return mem;
}

__attribute__((noipa)) void *lbmk_heap_reallocated(void *old_mem, void *new_mem, size_t size){
    if(new_mem || 0 == size) remove_block(old_mem);
    add_block(new_mem, size);
    return new_mem;
}

__attribute__((noipa)) void *lbmk_heap_freed(void *mem){
    remove_block(mem);
    return mem;
}

//The wrappers, linked in only for the functions the firmware calls. noipa: a call to them stays a call.
__attribute__((noipa)) void *__wrap_malloc(size_t size){
    return lbmk_heap_allocated(__real_malloc(size), size);
}

__attribute__((noipa)) void *__wrap_calloc(size_t count, size_t size){
    return lbmk_heap_allocated(__real_calloc(count, size), count * size);
}

__attribute__((noipa)) void *__wrap_realloc(void *mem, size_t size){
    return lbmk_heap_reallocated(mem, __real_realloc(mem, size), size);
}

__attribute__((noipa)) void __wrap_free(void *mem){
    __real_free(lbmk_heap_freed(mem));
}
