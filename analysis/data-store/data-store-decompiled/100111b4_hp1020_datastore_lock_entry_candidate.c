/* Function: 100111b4 hp1020_datastore_lock_entry_candidate */


/* high confidence: Locks indexed data-store entry and returns its value pointer */

undefined4 hp1020_datastore_lock_entry_candidate(int param_1)

{
  threadx_memory_or_copy_candidate(hp1020_datastore_lock_table_ptr + param_1 * 0x1c,0xffffffff);
  return *(undefined4 *)(hp1020_datastore_descriptor_table_ptr + param_1 * 0x18 + 4);
}


