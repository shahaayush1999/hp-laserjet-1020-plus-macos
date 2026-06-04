/* Function: 10007468 FUN_10007468 */


int FUN_10007468(int param_1,char *param_2,int param_3,int param_4,int param_5)

{
  bool bVar1;
  bool bVar2;
  undefined1 *puVar3;
  undefined *puVar4;
  undefined *puVar5;
  undefined4 uVar6;
  uint uVar7;
  code *pcVar8;
  char *pcVar9;
  int iVar10;
  char cVar11;
  uint uVar12;
  int iStack_38;
  char *pcStack_34;
  int iStack_30;
  
  *(undefined4 *)PTR_DAT_10005d1c = 0;
  puVar4 = PTR_DAT_10005d18;
  if (param_1 == 0) {
    *(undefined **)PTR_DAT_10005d34 = PTR_FUN_10005d6c;
  }
  else {
    *(undefined **)PTR_DAT_10005d34 = PTR_FUN_10005d70;
    *(int *)puVar4 = param_1;
  }
  puVar4 = PTR_DAT_10005d34;
  pcStack_34 = param_2;
  iStack_30 = param_1;
  if (*param_2 == '\n') {
    (**(code **)PTR_DAT_10005d34)(0xd);
    cVar11 = *pcStack_34;
    pcStack_34 = pcStack_34 + 1;
    (**(code **)puVar4)(cVar11);
  }
  puVar4 = PTR_DAT_10005d34;
  cVar11 = *pcStack_34;
  puVar3 = PTR_DAT_10005d38;
  while( true ) {
    PTR_DAT_10005d38 = puVar3;
    if (cVar11 == '\0') {
      if (iStack_30 != 0) {
        FUN_10007038(0);
      }
      return *(int *)PTR_DAT_10005d1c + -1;
    }
    iStack_38 = param_5;
    if (*pcStack_34 == '%') break;
    if ((*pcStack_34 == '\n') && (pcStack_34[-1] != '\r')) {
      (**(code **)puVar4)();
    }
    cVar11 = *pcStack_34;
LAB_1000769e:
    pcVar8 = *(code **)puVar4;
LAB_100076a1:
    (*pcVar8)(cVar11);
switchD_1000757d_caseD_24:
    cVar11 = pcStack_34[1];
    param_5 = iStack_38;
    puVar3 = PTR_DAT_10005d38;
    pcStack_34 = pcStack_34 + 1;
  }
  bVar2 = false;
  bVar1 = false;
  *(undefined4 *)PTR_DAT_10005d50 = 0;
  puVar5 = PTR_DAT_10005d54;
  *(undefined4 *)PTR_DAT_10005d28 = 0;
  uVar6 = DAT_10005d74;
  *puVar3 = 0x20;
  *(undefined4 *)puVar5 = uVar6;
  do {
    while( true ) {
      pcVar9 = pcStack_34 + 1;
      uVar12 = (uint)(byte)pcStack_34[1];
      if ((PTR_DAT_10005d68[uVar12] & 4) == 0) break;
      if (bVar1) {
        pcStack_34 = pcVar9;
        uVar6 = FUN_100073b8(&pcStack_34);
        *(undefined4 *)PTR_DAT_10005d54 = uVar6;
      }
      else {
        if (uVar12 == 0x30) {
          *PTR_DAT_10005d38 = pcStack_34[1];
        }
        pcStack_34 = pcVar9;
        uVar6 = FUN_100073b8(&pcStack_34);
        puVar5 = PTR_DAT_10005d28;
        *(undefined4 *)PTR_DAT_10005d30 = uVar6;
        *(undefined4 *)puVar5 = 1;
      }
      pcStack_34 = pcStack_34 + -1;
    }
    uVar7 = uVar12 + 0x20;
    if ((PTR_DAT_10005d68[uVar12] & 1) == 0) {
      uVar7 = uVar12;
    }
    pcStack_34 = pcVar9;
    switch(uVar7) {
    case 0x23:
      (**(code **)puVar4)(0x30);
      (**(code **)puVar4)(0x78);
      break;
    default:
      goto switchD_1000757d_caseD_24;
    case 0x25:
      pcVar8 = *(code **)puVar4;
      cVar11 = '%';
      goto LAB_100076a1;
    case 0x2d:
      *(undefined4 *)PTR_DAT_10005d50 = 1;
      break;
    case 0x2e:
      bVar1 = true;
      break;
    case 99:
      iStack_38 = param_5 + 4;
      iVar10 = param_4;
      if ((0x18 < iStack_38) && (iVar10 = param_3, param_5 < 0x18)) {
        iStack_38 = 0x1c;
      }
      cVar11 = *(char *)(iVar10 + iStack_38 + -1);
      goto LAB_1000769e;
    case 100:
      if ((bVar2) || (uVar12 == 0x44)) {
        if (0x18 < param_5 + 4) goto LAB_100075c4;
LAB_100075be:
        iStack_38 = param_5 + 4;
        iVar10 = param_4;
      }
      else {
        if (param_5 + 4 < 0x19) goto LAB_100075be;
LAB_100075c4:
        iStack_38 = param_5 + 4;
        iVar10 = param_3;
        if (param_5 < 0x18) {
          iStack_38 = 0x1c;
        }
      }
      FUN_10007180(*(undefined4 *)(iVar10 + iStack_38 + -4));
      goto switchD_1000757d_caseD_24;
    case 0x6c:
      bVar2 = true;
      break;
    case 0x73:
      iStack_38 = param_5 + 4;
      iVar10 = param_4;
      if ((0x18 < iStack_38) && (iVar10 = param_3, param_5 < 0x18)) {
        iStack_38 = 0x1c;
      }
      FUN_100070e0(*(undefined4 *)(iVar10 + iStack_38 + -4));
      goto switchD_1000757d_caseD_24;
    case 0x75:
      if ((bVar2) || (uVar12 == 0x55)) {
        if (0x18 < param_5 + 4) goto LAB_10007601;
LAB_100075fc:
        iStack_38 = param_5 + 4;
        iVar10 = param_4;
      }
      else {
        if (param_5 + 4 < 0x19) goto LAB_100075fc;
LAB_10007601:
        iStack_38 = param_5 + 4;
        iVar10 = param_3;
        if (param_5 < 0x18) {
          iStack_38 = 0x1c;
        }
      }
      FUN_100072b0(*(undefined4 *)(iVar10 + iStack_38 + -4),10);
      goto switchD_1000757d_caseD_24;
    case 0x78:
      iStack_38 = param_5 + 4;
      iVar10 = param_4;
      if ((0x18 < iStack_38) && (iVar10 = param_3, param_5 < 0x18)) {
        iStack_38 = 0x1c;
      }
      FUN_100072b0(*(undefined4 *)(iVar10 + iStack_38 + -4),0x10);
      goto switchD_1000757d_caseD_24;
    }
  } while( true );
}


