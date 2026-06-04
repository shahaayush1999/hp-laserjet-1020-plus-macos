/* Function: 10011178 hp1020_datastore_get_value_candidate */


/* high confidence: Get byte/halfword/word value from indexed firmware data-store entry */

uint hp1020_datastore_get_value_candidate(int param_1)

{
  int iVar1;
  
  iVar1 = *(int *)(hp1020_datastore_descriptor_table_ptr + param_1 * 0x18 + 8);
  if (iVar1 - 3U < 2) {
    return 0xffffffff;
  }
  if (iVar1 == 1) {
    return (uint)**(ushort **)(hp1020_datastore_descriptor_table_ptr + param_1 * 0x18 + 4);
  }
  if (iVar1 == 0) {
    return (uint)**(byte **)(hp1020_datastore_descriptor_table_ptr + param_1 * 0x18 + 4);
  }
  if (iVar1 != 2) {
    return param_1 * 3;
  }
  return **(uint **)(hp1020_datastore_descriptor_table_ptr + param_1 * 0x18 + 4);
}


