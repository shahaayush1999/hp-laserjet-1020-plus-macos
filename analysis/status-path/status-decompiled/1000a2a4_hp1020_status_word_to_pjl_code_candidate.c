/* Function: 1000a2a4 hp1020_status_word_to_pjl_code_candidate */


/* WARNING: Control flow encountered bad instruction data */
/* high confidence: Converts internal status word to PJL CODE value */

int hp1020_status_word_to_pjl_code_candidate(uint param_1)

{
  undefined4 *puVar1;
  int iVar2;
  int iVar3;
  
  puVar1 = (undefined4 *)hp1020_datastore_lock_entry_candidate(0x1f);
  iVar3 = DAT_10006018;
  if (((param_1 & 0xffff & DAT_10005f74) != 0x100) &&
     (((param_1 & DAT_10005e74) == 0 || ((param_1 & DAT_10005e34) != 0)))) {
    if ((param_1 & 0xffff) != DAT_10005f70) {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
    iVar2 = hp1020_status_code_offset_lookup_candidate(*puVar1);
    iVar3 = iVar2 + DAT_1000601c;
    if (puVar1[2] != 0) {
      iVar3 = (puVar1[2] + 1) * 100 + iVar2 + DAT_1000601c;
    }
  }
  hp1020_datastore_unlock_entry_candidate(0x1f);
  return iVar3;
}


