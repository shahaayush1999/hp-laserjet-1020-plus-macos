/* Function: 1000e1dc FUN_1000e1dc */


void FUN_1000e1dc(int param_1)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  char cVar6;
  undefined4 uVar5;
  undefined *puVar7;
  uint uVar8;
  int iVar9;
  bool bVar11;
  undefined4 uVar10;
  undefined *local_30;
  
  FUN_1000da5c();
  puVar7 = PTR_DAT_10006288;
  iVar3 = 0;
  local_30 = (undefined *)0x0;
  if ((*(int *)(PTR_DAT_10006288 + 0xac) == 0) && (*(int *)(PTR_DAT_10006288 + 0xa4) == 4)) {
    iVar2 = FUN_1001684c(PTR_DAT_10006288,*(undefined4 *)(PTR_PTR_10006274 + 0x28));
    iVar3 = 0;
    if (iVar2 == 0) {
      iVar3 = hp1020_alloc_buffer_candidate(0x51);
      hp1020_copy_string_candidate(iVar3,PTR_DAT_100062ac);
      FUN_1000da5c();
    }
    else {
      *(undefined4 *)(puVar7 + 0xac) = 0x15;
    }
  }
  puVar7 = (undefined *)0x0;
  iVar2 = 0;
  if (*(int *)(PTR_DAT_10006288 + 0xac) != 0) goto switchD_1000e359_caseD_0;
  uVar8 = *(uint *)(PTR_DAT_10006288 + 0xa4);
  iVar4 = 0;
  if (uVar8 == 3) {
    if (((param_1 == 3) || (param_1 == 0)) || (param_1 == 4)) {
      local_30 = PTR_DAT_100062ac;
      iVar2 = *(int *)(PTR_DAT_10006288 + 0xa8);
      puVar7 = PTR_DAT_10006288;
    }
    else {
      FUN_1000dda8(9);
      iVar9 = FUN_1000cd64();
      iVar2 = 0;
      iVar4 = 0x17;
      puVar7 = (undefined *)0x0;
      if (iVar9 != 0) {
        iVar4 = iVar9;
      }
    }
  }
  else if (uVar8 < 4) {
    if (uVar8 == 0) {
LAB_1000e280:
      iVar2 = 0;
      iVar4 = 0x17;
      puVar7 = (undefined *)0x0;
    }
  }
  else if ((uVar8 == 5) && (puVar7 = PTR_DAT_10006288, 1 < param_1 - 1U)) {
    FUN_1000dda8(7);
    goto LAB_1000e280;
  }
  puVar1 = PTR_DAT_1000626c;
  if (iVar4 != 0) goto switchD_1000e359_caseD_0;
  iVar4 = 0;
  if (*PTR_DAT_1000626c == '\0') {
    do {
      hp1020_pjl_read_or_poll_candidate();
      iVar9 = *(int *)PTR_DAT_10006270;
      if ((iVar9 != 0x20) && (iVar9 != 9)) {
        if (*puVar1 != '\0') break;
        if (iVar9 < 0x21) {
          if (iVar9 != -1) {
            FUN_1000dd60();
          }
          iVar4 = 6;
        }
        else {
          iVar4 = 0x18;
        }
      }
      if ((*puVar1 != '\0') || (iVar4 != 0)) break;
    } while( true );
  }
  if (iVar4 != 0) goto switchD_1000e359_caseD_0;
  bVar11 = false;
  if ((param_1 - 1U < 2) && (cVar6 = FUN_1000c69c(param_1 == 1,iVar3,puVar7), cVar6 == '\0')) {
    bVar11 = true;
  }
  if ((bVar11) || (((param_1 != 3 && (param_1 != 0)) && (param_1 != 4))))
  goto switchD_1000e359_caseD_0;
  uVar5 = FUN_1000b808(iVar3,puVar7);
  uVar8 = 0;
  uVar10 = 0;
  switch(uVar5) {
  case 0:
    uVar10 = 4;
    break;
  case 1:
    uVar10 = 6;
    goto LAB_1000e348;
  case 2:
    if (iVar2 != 2) goto LAB_1000e345;
LAB_1000e32c:
    bVar11 = false;
    if (param_1 == 0) {
      bVar11 = true;
    }
LAB_1000e334:
    uVar8 = FUN_1000c8fc(bVar11,iVar3,puVar7,local_30);
    break;
  case 3:
    if (iVar2 - 6U < 2) goto LAB_1000e32c;
    goto LAB_1000e345;
  case 4:
    if (iVar2 == 1) {
      bVar11 = param_1 == 0;
      goto LAB_1000e334;
    }
LAB_1000e345:
    uVar10 = 8;
LAB_1000e348:
    FUN_1000dda8(uVar10);
    uVar8 = 0;
    uVar10 = 0x17;
  }
  if (uVar8 < 7) {
                    /* WARNING: Could not recover jumptable at 0x1000e359. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (**(code **)(uVar8 * 4 + DAT_100062cc))(uVar10);
    return;
  }
switchD_1000e359_caseD_0:
  if (iVar3 != 0) {
    FUN_1000dc24(iVar3);
  }
  return;
}


