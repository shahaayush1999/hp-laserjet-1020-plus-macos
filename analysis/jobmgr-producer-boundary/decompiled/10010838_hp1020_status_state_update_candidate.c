/* Function: 10010838 hp1020_status_state_update_candidate */


void hp1020_status_state_update_candidate(uint param_1,int param_2)

{
  bool bVar1;
  bool bVar2;
  undefined *puVar3;
  uint uVar4;
  bool bVar5;
  undefined4 local_50;
  uint *puStack_4c;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  uint auStack_30 [12];

  puVar3 = PTR_DAT_100063d8;
  bVar2 = false;
  bVar5 = false;
  uVar4 = *(uint *)(PTR_DAT_100063d8 + 4);
  bVar1 = false;
  auStack_30[0] = param_1;
  if (uVar4 == 3) {
    if ((param_1 & DAT_10005f74) == 0x100) {
      if (param_2 != 10) goto LAB_1001098d;
LAB_10010941:
      bVar1 = true;
      *(undefined4 *)(puVar3 + 4) = 2;
      goto LAB_1001098d;
    }
    if ((param_1 & 0xffff) != DAT_1000641c) {
      if ((param_1 & DAT_10005e34) == 0) {
        if ((param_1 & DAT_10005f74) == DAT_10006418) {
          bVar1 = true;
          *(uint *)(PTR_DAT_100063d8 + 0x10) = param_1;
        }
        else if ((*(uint *)(PTR_DAT_100063d8 + 0xc) & DAT_10006378) < (param_1 & DAT_10006378)) {
          *(uint *)(PTR_DAT_100063d8 + 0xc) = param_1;
          bVar2 = true;
        }
        goto LAB_1001098d;
      }
LAB_100108db:
      *PTR_DAT_100063d8 = 0;
      bVar1 = true;
      bVar5 = true;
      *(undefined4 *)(puVar3 + 4) = 4;
      goto LAB_1001098d;
    }
  }
  else if (uVar4 < 4) {
    if ((uVar4 != 2) ||
       ((uVar4 = param_1 & DAT_10005f74, uVar4 == 0x100 &&
        ((*(uint *)(PTR_DAT_100063d8 + 8) & DAT_10005f74) == 0x100)))) goto LAB_1001098d;
    if (param_1 != DAT_10006048) {
      if (uVar4 == DAT_10006418) {
        bVar1 = true;
        *(undefined4 *)(PTR_DAT_100063d8 + 4) = 3;
        *(undefined4 *)(puVar3 + 0xc) = 0;
        *(uint *)(puVar3 + 0x10) = param_1;
        goto LAB_1001098d;
      }
      if ((param_1 & DAT_10005e34) != 0) goto LAB_100108db;
      if ((param_1 == *(uint *)(PTR_DAT_100063d8 + 8)) ||
         ((uVar4 != 0x100 &&
          ((param_1 & DAT_10006378) < (*(uint *)(PTR_DAT_100063d8 + 8) & DAT_10006378)))))
      goto LAB_1001098d;
    }
  }
  else {
    if (uVar4 != 4) goto LAB_1001098d;
    uVar4 = param_1 & DAT_10005f74;
    if ((uVar4 == 0x100) || ((param_1 & DAT_10005e34) == 0)) {
      if (param_2 != *(int *)(PTR_DAT_100063d8 + 0x14)) {
        if (uVar4 == DAT_10006418) {
          if ((param_1 & 0x10) == 0) {
            *(uint *)(PTR_DAT_100063d8 + 0x10) = param_1;
          }
          else {
            bVar1 = (*(uint *)(PTR_DAT_100063d8 + 8) & DAT_10005f74) == 0x1000;
          }
        }
        goto LAB_1001098d;
      }
      *PTR_DAT_100063d8 = 1;
      bVar1 = true;
      bVar5 = true;
      if (puVar3[0x18] != '\0') {
        *(undefined4 *)(puVar3 + 4) = 3;
        auStack_30[0] = *(uint *)(puVar3 + 0x10);
        *(undefined4 *)(puVar3 + 0xc) = 0;
        goto LAB_1001098d;
      }
      goto LAB_10010941;
    }
    if (uVar4 != DAT_10006420) {
      if (((*(uint *)(PTR_DAT_100063d8 + 8) & DAT_10006378) <= (param_1 & DAT_10006378)) &&
         (bVar1 = true, (param_1 & 0xffff) == (*(uint *)(PTR_DAT_100063d8 + 8) & 0xffff))) {
        bVar1 = false;
      }
      goto LAB_1001098d;
    }
  }
  bVar1 = true;
LAB_1001098d:
  if (bVar5) {
    local_50 = 0x18;
    puStack_4c = (uint *)0x0;
    FUN_10010f54(&local_50);
    puStack_4c = (uint *)PTR_DAT_100063d8;
    FUN_10010fd0(&local_50);
    bVar2 = true;
  }
  puVar3 = PTR_DAT_100063d8;
  if ((bVar1) && (auStack_30[0] != *(uint *)(PTR_DAT_100063d8 + 8))) {
    *(uint *)(PTR_DAT_100063d8 + 8) = auStack_30[0];
    uVar4 = DAT_10005c84;
    *(int *)(puVar3 + 0x14) = param_2;
    if ((auStack_30[0] & uVar4) != 0) {
      uStack_40 = 0xf;
      if (((auStack_30[0] & DAT_10005f74) == DAT_10005f78) ||
         ((auStack_30[0] & 0xffff) == DAT_10006424)) {
        uStack_3c = 3;
      }
      else if ((auStack_30[0] & DAT_10006380) == 0) {
        uStack_3c = 4;
      }
      else {
        uStack_3c = 1;
      }
      hp1020_queue_send_candidate(3,&uStack_40);
    }
    FUN_10010a8c(auStack_30[0]);
    local_50 = 0x19;
    puStack_4c = (uint *)0x0;
    FUN_10010f54(&local_50);
    puStack_4c = auStack_30;
    FUN_10010fd0(&local_50);
    bVar2 = true;
  }
  if ((auStack_30[0] & DAT_10005e74) != 0) {
    bVar2 = false;
  }
  if (bVar2) {
    FUN_10010a3c();
  }
  return;
}
