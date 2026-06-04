/* Function: 1000b870 hp1020_pjl_status_table_get_candidate */


/* high confidence: Reads values from PJL/status command table */

undefined4 hp1020_pjl_status_table_get_candidate(char param_1,ushort param_2)

{
  undefined4 uVar1;
  undefined1 auStack_40 [16];
  undefined4 uStack_30;
  undefined1 *puStack_2c;
  
  puStack_2c = auStack_40;
  if ((1 < *(int *)(PTR_DAT_10006148 + (uint)param_2 * 0x24 + 0x14) - 6U) &&
     (*(int *)(PTR_DAT_10006148 + (uint)param_2 * 0x24 + 0x14) != 2)) {
    return 0;
  }
  if (0x13 < param_2) {
    return 0;
  }
  switch(*(undefined4 *)(PTR_DAT_10006148 + (uint)param_2 * 0x24)) {
  case 0:
    uVar1 = hp1020_datastore_get_value_candidate(10);
    return uVar1;
  case 1:
    uVar1 = hp1020_datastore_get_value_candidate(9);
    return uVar1;
  case 2:
    uVar1 = hp1020_datastore_get_value_candidate(0xf);
    return uVar1;
  case 3:
    break;
  case 4:
    uStack_30 = 4;
    hp1020_datastore_read_locked_candidate(&uStack_30);
    hp1020_datastore_unlock_entry_candidate(4);
    uVar1 = FUN_100167f4(auStack_40);
    return uVar1;
  case 5:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x24);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0xd);
    return uVar1;
  case 6:
    return 0;
  case 7:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x10);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0x10);
    return uVar1;
  case 8:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x11);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0x11);
    return uVar1;
  case 9:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x12);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0x12);
    return uVar1;
  case 10:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x13);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0x13);
    return uVar1;
  case 0xb:
    if (param_1 == '\0') {
      uVar1 = hp1020_datastore_get_value_candidate(0x14);
      return uVar1;
    }
    uVar1 = hp1020_datastore_get_value_candidate(0x14);
    return uVar1;
  default:
    return 0;
  }
  if (param_1 == '\0') {
    uVar1 = hp1020_datastore_get_value_candidate(0x25);
    return uVar1;
  }
  uVar1 = hp1020_datastore_get_value_candidate(0x25);
  return uVar1;
}


