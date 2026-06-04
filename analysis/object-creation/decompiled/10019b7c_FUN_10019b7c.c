/* Function: 10019b7c FUN_10019b7c */


undefined4 FUN_10019b7c(int param_1,undefined4 *param_2,int param_3)

{
  undefined *puVar1;
  uint uVar2;
  int iVar3;
  undefined4 *puVar4;
  int iVar5;
  undefined4 *puVar6;
  undefined4 *puVar7;
  undefined4 *puVar8;
  undefined4 *puVar9;
  int iVar10;
  undefined4 uVar11;
  undefined4 local_60;
  undefined4 local_5c;
  undefined4 local_58;
  undefined4 local_54;
  undefined4 local_50;
  undefined4 local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40 [16];
  
  puVar9 = &local_60;
  puVar6 = &local_60;
  puVar7 = &local_60;
  puVar8 = &local_60;
  iVar10 = 0;
  uVar11 = rsil(1);
  if (*(int *)(param_1 + 0x14) == 0) {
    if (param_3 != 0) {
      if (*(int *)(param_1 + 0x24) == *(int *)(param_1 + 0x18)) {
        *(int *)(param_1 + 0x24) = *(int *)(param_1 + 0x1c) + *(int *)(param_1 + 8) * -4;
      }
      else {
        *(int *)(param_1 + 0x24) = *(int *)(param_1 + 0x24) + *(int *)(param_1 + 8) * -4;
      }
      puVar4 = *(undefined4 **)(param_1 + 0x24);
      iVar10 = 1;
      *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + 1;
      uVar2 = *(uint *)(param_1 + 8);
      *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + -1;
      if (uVar2 == 2) {
LAB_10019c48:
        *puVar7 = *puVar4;
        puVar4 = puVar4 + 1;
        puVar8 = puVar7 + 1;
      }
      else {
        if (2 < uVar2) {
          if (uVar2 != 4) {
            if (uVar2 != 8) goto LAB_10019bd8;
            goto LAB_10019c18;
          }
LAB_10019c38:
          *puVar6 = *puVar4;
          puVar6[1] = puVar4[1];
          puVar4 = puVar4 + 2;
          puVar7 = puVar6 + 2;
          goto LAB_10019c48;
        }
        if (uVar2 != 1) {
LAB_10019bd8:
          local_60 = *puVar4;
          local_5c = puVar4[1];
          local_58 = puVar4[2];
          local_54 = puVar4[3];
          local_50 = puVar4[4];
          local_4c = puVar4[5];
          local_48 = puVar4[6];
          local_44 = puVar4[7];
          puVar4 = puVar4 + 8;
          puVar9 = local_40;
LAB_10019c18:
          *puVar9 = *puVar4;
          puVar9[1] = puVar4[1];
          puVar9[2] = puVar4[2];
          puVar9[3] = puVar4[3];
          puVar4 = puVar4 + 4;
          puVar6 = puVar9 + 4;
          goto LAB_10019c38;
        }
      }
      *puVar8 = *puVar4;
    }
    if (*(int *)(param_1 + 0x14) == 0) {
      wsr(0,uVar11);
      rsync();
      return 0xb;
    }
  }
  iVar5 = *(int *)(param_1 + 0x28);
  if (iVar5 != 0) {
    if (iVar5 == *(int *)(iVar5 + 0x70)) {
      *(undefined4 *)(param_1 + 0x28) = 0;
    }
    else {
      *(int *)(param_1 + 0x28) = *(int *)(iVar5 + 0x70);
      *(undefined4 *)(*(int *)(iVar5 + 0x70) + 0x74) = *(undefined4 *)(iVar5 + 0x74);
      *(undefined4 *)(*(int *)(iVar5 + 0x74) + 0x70) = *(undefined4 *)(iVar5 + 0x70);
    }
    puVar1 = PTR_DAT_10006ac0;
    *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + -1;
    iVar3 = *(int *)puVar1;
    *(undefined4 *)(iVar5 + 0x68) = 0;
    *(int *)puVar1 = iVar3 + 1;
    wsr(0,uVar11);
    rsync();
    puVar9 = *(undefined4 **)(iVar5 + 0x7c);
    uVar2 = *(uint *)(param_1 + 8);
    if (uVar2 != 2) {
      if (uVar2 < 3) {
        if (uVar2 == 1) goto LAB_10019e7a;
LAB_10019e02:
        *puVar9 = *param_2;
        puVar9[1] = param_2[1];
        puVar9[2] = param_2[2];
        puVar9[3] = param_2[3];
        puVar9[4] = param_2[4];
        puVar9[5] = param_2[5];
        puVar9[6] = param_2[6];
        puVar9[7] = param_2[7];
        param_2 = param_2 + 8;
        puVar9 = puVar9 + 8;
LAB_10019e42:
        *puVar9 = *param_2;
        puVar9[1] = param_2[1];
        puVar9[2] = param_2[2];
        puVar9[3] = param_2[3];
        param_2 = param_2 + 4;
        puVar9 = puVar9 + 4;
      }
      else if (uVar2 != 4) {
        if (uVar2 != 8) goto LAB_10019e02;
        goto LAB_10019e42;
      }
      *puVar9 = *param_2;
      puVar9[1] = param_2[1];
      param_2 = param_2 + 2;
      puVar9 = puVar9 + 2;
    }
    *puVar9 = *param_2;
    param_2 = param_2 + 1;
    puVar9 = puVar9 + 1;
LAB_10019e7a:
    *puVar9 = *param_2;
    if (*(int *)(iVar5 + 100) == 0) {
      *(undefined4 *)(iVar5 + 0x4c) = 0;
    }
    else {
      FUN_1001bac4(iVar5 + 0x4c,puVar9,iVar10,uVar11);
    }
    *(undefined4 *)(iVar5 + 0x84) = 0;
    iVar10 = rtos_thread_ready_insert_candidate(iVar5);
    if (iVar10 != 0) {
      FUN_10018750();
    }
    return 0;
  }
  if (*(int *)(param_1 + 0x20) == *(int *)(param_1 + 0x18)) {
    *(int *)(param_1 + 0x20) = *(int *)(param_1 + 0x1c) + *(int *)(param_1 + 8) * -4;
  }
  else {
    *(int *)(param_1 + 0x20) = *(int *)(param_1 + 0x20) + *(int *)(param_1 + 8) * -4;
  }
  puVar9 = *(undefined4 **)(param_1 + 0x20);
  *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + -1;
  uVar2 = *(uint *)(param_1 + 8);
  *(int *)(param_1 + 0x10) = *(int *)(param_1 + 0x10) + 1;
  if (uVar2 != 2) {
    if (uVar2 < 3) {
      if (uVar2 == 1) goto LAB_10019d20;
LAB_10019ca8:
      *puVar9 = *param_2;
      puVar9[1] = param_2[1];
      puVar9[2] = param_2[2];
      puVar9[3] = param_2[3];
      puVar9[4] = param_2[4];
      puVar9[5] = param_2[5];
      puVar9[6] = param_2[6];
      puVar9[7] = param_2[7];
      param_2 = param_2 + 8;
      puVar9 = puVar9 + 8;
LAB_10019ce8:
      *puVar9 = *param_2;
      puVar9[1] = param_2[1];
      puVar9[2] = param_2[2];
      puVar9[3] = param_2[3];
      param_2 = param_2 + 4;
      puVar9 = puVar9 + 4;
    }
    else if (uVar2 != 4) {
      if (uVar2 != 8) goto LAB_10019ca8;
      goto LAB_10019ce8;
    }
    *puVar9 = *param_2;
    puVar9[1] = param_2[1];
    param_2 = param_2 + 2;
    puVar9 = puVar9 + 2;
  }
  *puVar9 = *param_2;
  param_2 = param_2 + 1;
  puVar9 = puVar9 + 1;
LAB_10019d20:
  *puVar9 = *param_2;
  puVar1 = PTR_LAB_10006b84;
  if (iVar10 == 0) {
    wsr(0,uVar11);
    rsync();
    return 0;
  }
  iVar10 = *(int *)PTR_DAT_10006a9c;
  *(int *)(iVar10 + 0x6c) = param_1;
  *(undefined4 **)(iVar10 + 0x7c) = &local_60;
  *(undefined **)(iVar10 + 0x68) = puVar1;
  if (*(int *)(param_1 + 0x28) == 0) {
    *(int *)(param_1 + 0x28) = iVar10;
    *(int *)(iVar10 + 0x70) = iVar10;
    *(int *)(iVar10 + 0x74) = iVar10;
  }
  else {
    *(int *)(iVar10 + 0x70) = *(int *)(param_1 + 0x28);
    *(undefined4 *)(iVar10 + 0x74) = *(undefined4 *)(*(int *)(param_1 + 0x28) + 0x74);
    *(int *)(*(int *)(*(int *)(param_1 + 0x28) + 0x74) + 0x70) = iVar10;
    *(int *)(*(int *)(param_1 + 0x28) + 0x74) = iVar10;
    *(int *)(param_1 + 0x28) = iVar10;
  }
  puVar1 = PTR_DAT_10006ac0;
  *(int *)(param_1 + 0x2c) = *(int *)(param_1 + 0x2c) + 1;
  *(undefined4 *)(iVar10 + 0x30) = 5;
  *(undefined4 *)(iVar10 + 0x38) = 1;
  iVar5 = *(int *)puVar1;
  *(int *)(iVar10 + 0x4c) = param_3;
  *(int *)puVar1 = iVar5 + 1;
  wsr(0,uVar11);
  rsync();
  if (param_3 != -1) {
    rtos_timer_insert_candidate(iVar10 + 0x4c);
  }
  rtos_schedule_candidate(iVar10);
  return *(undefined4 *)(iVar10 + 0x84);
}


