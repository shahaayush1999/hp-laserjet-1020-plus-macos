/* Function: 1000d700 FUN_1000d700 */


int FUN_1000d700(void)

{
  bool bVar1;
  bool bVar2;
  undefined *puVar3;
  undefined *puVar4;
  int iVar5;
  int iVar6;
  int *piVar7;
  undefined1 *puVar8;
  undefined4 uVar9;
  bool bVar10;
  undefined1 local_80 [128];
  
  puVar4 = PTR_PTR_10006274;
  *PTR_DAT_1000626c = 0;
  uVar9 = *(undefined4 *)(puVar4 + 4);
  *(undefined4 *)PTR_DAT_1000629c = 0;
  iVar5 = FUN_100169d4(uVar9);
  puVar3 = PTR_DAT_10006270;
  iVar6 = 0;
  bVar2 = false;
  if (0 < iVar5) {
    do {
      FUN_1000d6b0();
      if (*(uint *)puVar3 != (uint)*(byte *)(*(int *)(puVar4 + 4) + iVar6)) {
        if (*(uint *)puVar3 != 0xffffffff) {
          FUN_1000dd60();
        }
        while (iVar6 = iVar6 + -1, -1 < iVar6) {
          FUN_1000dd60(*(undefined1 *)(*(int *)(puVar4 + 4) + iVar6));
        }
        return -4;
      }
      iVar6 = iVar6 + 1;
    } while (iVar6 < iVar5);
  }
  FUN_1000d6b0();
  iVar6 = *(int *)PTR_DAT_10006270;
  if (iVar6 == 10) {
    return -1;
  }
  if ((iVar6 != 0x20) && (iVar6 != 9)) {
    puVar3 = PTR_PTR_10006274;
    if (iVar6 != -1) {
      FUN_1000dd60();
      puVar3 = PTR_PTR_10006274;
    }
    while (puVar4 = PTR_PTR_10006274, iVar5 = iVar5 + -1, -1 < iVar5) {
      piVar7 = (int *)(PTR_PTR_10006274 + 4);
      PTR_PTR_10006274 = puVar3;
      FUN_1000dd60(*(undefined1 *)(*piVar7 + iVar5));
      puVar3 = PTR_PTR_10006274;
      PTR_PTR_10006274 = puVar4;
    }
    PTR_PTR_10006274 = puVar3;
    return -4;
  }
  FUN_1000af88();
  puVar3 = PTR_DAT_10006270;
  iVar6 = 0;
  bVar1 = false;
  do {
    FUN_1000d6b0();
    iVar5 = *(int *)puVar3;
    if (iVar5 == 10) {
      bVar1 = true;
      bVar10 = false;
    }
    else if (iVar5 - 0x30U < 10) {
      if (iVar6 == 0) {
        return -3;
      }
LAB_1000d7e6:
      bVar10 = true;
    }
    else if (iVar5 - 0x61U < 0x1a) {
      bVar10 = true;
      *(int *)puVar3 = iVar5 + -0x20;
    }
    else {
      if (iVar5 - 0x41U < 0x1a) goto LAB_1000d7e6;
      if ((iVar5 != 0x20) && (iVar5 != 9)) {
        if (0x20 < iVar5) {
          return -3;
        }
        if (iVar5 != -1) {
          FUN_1000dd60();
        }
        return -5;
      }
      bVar10 = false;
      bVar1 = iVar6 != 0;
    }
    if (bVar10) {
      if (iVar6 < 0x50) {
        puVar8 = local_80 + iVar6;
        iVar6 = iVar6 + 1;
        *puVar8 = puVar3[3];
      }
      else if (!bVar2) {
        FUN_1000dda8(3);
        bVar2 = true;
      }
    }
    if (bVar1) {
      local_80[iVar6] = 0;
      FUN_1001693c(PTR_DAT_100062a0,local_80);
      if (iVar6 == 0) {
        return -1;
      }
      iVar5 = *(int *)PTR_PTR_100062a4;
      iVar6 = 0;
      piVar7 = (int *)PTR_PTR_100062a4;
      while( true ) {
        if (iVar5 == 0) {
          return -2;
        }
        iVar5 = FUN_1001684c(local_80,*piVar7);
        if (iVar5 == 0) break;
        piVar7 = piVar7 + 2;
        iVar5 = *piVar7;
        iVar6 = iVar6 + 1;
      }
      return iVar6;
    }
  } while( true );
}


