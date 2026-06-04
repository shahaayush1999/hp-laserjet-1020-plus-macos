/* Function: 1000f84c hp1020_print_mgr_media_select_candidate */


/* WARNING: Type propagation algorithm not settling */
/* print-manager fallout mapping candidate */

int hp1020_print_mgr_media_select_candidate(int param_1,int param_2)

{
  bool bVar1;
  bool bVar2;
  undefined *puVar3;
  undefined *puVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  int local_60;
  undefined4 uStack_5c;
  undefined4 uStack_58;
  undefined4 uStack_54;
  byte bStack_50;
  uint uStack_4c;
  int aiStack_48 [6];
  undefined4 uStack_30;

  uStack_4c = 4;
  local_60 = 0;
  aiStack_48[0] = 0;
  aiStack_48[1] = 0;
  aiStack_48[2] = 0;
  bStack_50 = 0;
  iVar5 = hp1020_datastore_lock_entry_candidate(0x1d);
  uStack_30 = hp1020_datastore_lock_entry_candidate(1);
  if (param_2 == 0) {
    uStack_58 = (uint)*(ushort *)(param_1 + 10);
    uStack_5c = (uint)*(ushort *)(param_1 + 0x10);
    uStack_54 = (uint)*(ushort *)(param_1 + 0xe);
    if (*(short *)(param_1 + 0x7a) == 0) {
      *(undefined4 *)PTR_DAT_1000636c = 0;
    }
    if ((((*(int *)PTR_DAT_1000636c == 1) && (uStack_58 == *(uint *)(PTR_DAT_1000636c + 8))) &&
        (uStack_5c == *(uint *)(PTR_DAT_1000636c + 4))) &&
       (uStack_54 == *(uint *)(PTR_DAT_1000636c + 0xc))) {
      uStack_58 = *(uint *)(PTR_DAT_1000636c + 0x14);
      uStack_5c = *(uint *)(PTR_DAT_1000636c + 0x10);
      uStack_54 = *(uint *)(PTR_DAT_1000636c + 0x18);
    }
    if ((uStack_54 < 3) && (*(int *)(iVar5 + uStack_54 * 0x70 + 0x38) == 0)) {
      *(undefined2 *)(param_1 + 0xe) = 3;
      uStack_54 = 3;
    }
  }
  else {
    uStack_58 = *(uint *)(hp1020_print_mgr_pending_media_ptr_word + 4);
    uStack_5c = *(uint *)hp1020_print_mgr_pending_media_ptr_word;
    uStack_54 = *(uint *)(hp1020_print_mgr_pending_media_ptr_word + 8);
  }
  FUN_1001005c(iVar5,&uStack_4c,aiStack_48,aiStack_48 + 1);
  bVar1 = false;
  bVar2 = false;
  iVar6 = 0;
  if (param_2 == 1) {
    iVar7 = *(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc);
    if (iVar7 - 4U < 2) {
      if (aiStack_48[0] != 0) {
        iVar6 = 0;
        uStack_54 = uStack_4c;
        bVar1 = true;
        goto LAB_1000f9c6;
      }
      if ((uStack_54 == 3) || (*(int *)(iVar5 + uStack_54 * 0x70 + 0x34) != 0)) {
        bVar1 = true;
        iVar6 = 0;
        goto LAB_1000f9c6;
      }
      if (iVar7 == 4) {
        bVar1 = true;
        iVar6 = 1;
        local_60 = 4;
        goto LAB_1000f9c6;
      }
    }
    else if (1 < iVar7 - 1U) goto LAB_1000f9c6;
    uStack_54 = 3;
    bVar2 = true;
    aiStack_48[2] = 1;
    goto LAB_1000f9c6;
  }
  if (param_2 == 0) {
    if ((*(char *)(param_1 + 0x76) == '\x01') && (*(int *)(PTR_DAT_1000633c + 0x10) == 0)) {
      local_60 = 4;
      iVar6 = 1;
      bVar1 = true;
      if (uStack_54 == 3) {
        uStack_54 = *(uint *)(PTR_DAT_1000633c + 8);
      }
    }
    goto LAB_1000f9c6;
  }
  if (param_2 == 2) {
    if (*(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc) == 3) {
LAB_1000f9ad:
      uStack_58 = (uint)*(ushort *)(param_1 + 10);
      uStack_5c = (uint)*(ushort *)(param_1 + 0x10);
      uStack_54 = (uint)*(ushort *)(param_1 + 0xe);
      goto LAB_1000f9c6;
    }
    iVar7 = 6;
  }
  else {
    if (param_2 != 3) goto LAB_1000f9c6;
    iVar7 = *(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc);
    if (iVar7 == 1) {
      if (*(uint *)(hp1020_print_mgr_pending_media_ptr_word + 8) == (uint)*(ushort *)(param_1 + 0xe)
         ) goto LAB_1000f9c6;
      goto LAB_1000f9ad;
    }
  }
  iVar6 = 1;
  bVar1 = true;
  local_60 = iVar7;
LAB_1000f9c6:
  if ((*(uint *)(iVar5 + 0x30) & 2) != 0) {
    uStack_54 = (uint)*(ushort *)(param_1 + 0xe);
  }
  if (uStack_58 != 0) {
    bStack_50 = bStack_50 | 2;
  }
  if (uStack_5c != 0) {
    bStack_50 = bStack_50 | 4;
  }
  if (1 < uStack_54 - 3) {
    bStack_50 = bStack_50 | 1;
  }
  if (!bVar1) {
    iVar6 = FUN_1000fabc(iVar5,uStack_30,&local_60);
  }
  puVar4 = hp1020_print_mgr_pending_media_ptr_word;
  puVar3 = PTR_DAT_1000633c;
  if (iVar6 == 0) {
    *(uint *)(PTR_DAT_1000633c + 4) = uStack_58;
    *(uint *)(puVar3 + 8) = uStack_54;
    *(uint *)puVar3 = uStack_5c;
    if (uStack_54 == uStack_4c) {
      *(undefined4 *)(puVar3 + 0xc) = 1;
    }
    else {
      *(undefined4 *)(puVar3 + 0xc) = 0;
    }
    if (*(char *)(param_1 + 0x77) == '\0') {
      *(undefined4 *)(PTR_DAT_1000633c + 0x10) = 0;
    }
    else {
      *(undefined4 *)(PTR_DAT_1000633c + 0x10) = 1;
    }
    puVar3 = PTR_DAT_1000636c;
    if (bVar2) {
      *(undefined4 *)PTR_DAT_1000636c = 1;
      *(uint *)(puVar3 + 8) = (uint)*(ushort *)(param_1 + 10);
      *(uint *)(puVar3 + 4) = (uint)*(ushort *)(param_1 + 0x10);
      *(uint *)(puVar3 + 0xc) = (uint)*(ushort *)(param_1 + 0xe);
      *(uint *)(puVar3 + 0x14) = uStack_58;
      *(uint *)(puVar3 + 0x10) = uStack_5c;
      *(uint *)(puVar3 + 0x18) = uStack_54;
    }
    *(undefined2 *)(param_1 + 0x7c) = uStack_54._2_2_;
    *(undefined2 *)(param_1 + 0x80) = uStack_5c._2_2_;
    *(undefined2 *)(param_1 + 0x7e) = uStack_58._2_2_;
    hp1020_print_mgr_clear_pending_media_candidate();
  }
  else {
    *(undefined4 *)PTR_DAT_1000636c = 0;
    *(int *)(puVar4 + 0xc) = local_60;
    *(uint *)(puVar4 + 8) = uStack_54;
    *(uint *)(puVar4 + 4) = uStack_58;
    *(uint *)puVar4 = uStack_5c;
    *(int *)(puVar4 + 0x10) = *(int *)(puVar4 + 0x10) + 1;
  }
  hp1020_datastore_unlock_entry_candidate(0x1d);
  hp1020_datastore_unlock_entry_candidate(1);
  return local_60;
}
