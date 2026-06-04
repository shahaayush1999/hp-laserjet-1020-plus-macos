/* Function: 100111b4 hp1020_datastore_lock_entry_candidate */


undefined4 hp1020_datastore_lock_entry_candidate(int param_1)

{
  threadx_memory_or_copy_candidate(PTR_DAT_10006464 + param_1 * 0x1c,0xffffffff);
  return *(undefined4 *)(PTR_DAT_1000647c + param_1 * 0x18 + 4);
}


