/* Function: 1001896c FUN_1001896c */


undefined4 FUN_1001896c(int param_1,uint param_2,uint param_3)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  int iVar9;
  undefined4 uVar10;
  uint uVar11;
  undefined1 uVar12;
  int local_40;
  
  uVar11 = 0;
  uVar10 = rsil(1);
  uVar12 = 0;
  if ((param_3 & 2) != 0) {
    *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & param_2;
    wsr(0,uVar10);
    rsync();
    return 0;
  }
  iVar6 = *(int *)(param_1 + 0x10);
  param_2 = *(uint *)(param_1 + 8) | param_2;
  *(uint *)(param_1 + 8) = param_2;
  if (iVar6 == 0) {
    if (*(int *)(param_1 + 0x14) != 0) {
      *(int *)(param_1 + 0xc) = *(int *)(param_1 + 0xc) + 1;
    }
    wsr(0,uVar10);
    rsync();
  }
  else {
    iVar4 = *(int *)(param_1 + 0x14);
    iVar5 = 0;
    if (iVar4 == 1) {
      if ((*(uint *)(iVar6 + 0x80) & 2) == 0) {
        iVar4 = 7;
        if ((param_2 & *(uint *)(iVar6 + 0x78)) != 0) {
          iVar4 = iVar5;
        }
      }
      else {
        iVar4 = 7;
        if ((param_2 & *(uint *)(iVar6 + 0x78)) == *(uint *)(iVar6 + 0x78)) {
          iVar4 = iVar5;
        }
      }
      if (iVar4 == 0) {
        **(undefined4 **)(iVar6 + 0x7c) = *(undefined4 *)(param_1 + 8);
        if ((*(uint *)(iVar6 + 0x80) & 1) != 0) {
          *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & (*(uint *)(iVar6 + 0x78) ^ 0xffffffff);
        }
        *(undefined4 *)(param_1 + 0x10) = 0;
        puVar1 = PTR_DAT_10006ac0;
        *(undefined4 *)(param_1 + 0x14) = 0;
        iVar5 = *(int *)puVar1;
        *(undefined4 *)(iVar6 + 0x68) = 0;
        *(int *)puVar1 = iVar5 + 1;
        wsr(0,uVar10);
        rsync();
        if (*(int *)(iVar6 + 100) == 0) {
          *(undefined4 *)(iVar6 + 0x4c) = 0;
        }
        else {
          FUN_1001bac4(iVar6 + 0x4c);
        }
        *(undefined4 *)(iVar6 + 0x84) = 0;
        iVar6 = FUN_1001aac0(iVar6);
        if (iVar6 != 0) {
          FUN_10018750();
        }
        return 0;
      }
      wsr(0,uVar10);
      rsync();
      return 0;
    }
    *(undefined4 *)(param_1 + 0x10) = 0;
    *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
    iVar2 = iVar5;
    iVar9 = iVar6;
    local_40 = iVar5;
    do {
      wsr(0,uVar10);
      rsync();
      uVar10 = rsil(1);
      iVar3 = iVar6;
      if (*(int *)(param_1 + 0xc) != 0) {
        *(undefined4 *)(param_1 + 0xc) = 0;
        iVar4 = *(int *)(param_1 + 0x14);
        param_2 = param_2 | *(uint *)(param_1 + 8);
        iVar3 = iVar9;
        if (iVar9 == 0) break;
      }
      uVar7 = *(uint *)(iVar3 + 0x80);
      if ((uVar7 & 2) == 0) {
        iVar8 = 7;
        if ((param_2 & *(uint *)(iVar3 + 0x78)) != 0) {
          iVar8 = 0;
        }
      }
      else {
        iVar8 = 7;
        if ((param_2 & *(uint *)(iVar3 + 0x78)) == *(uint *)(iVar3 + 0x78)) {
          iVar8 = iVar5;
        }
      }
      iVar6 = *(int *)(iVar3 + 0x70);
      if (iVar8 == 0) {
        **(uint **)(iVar3 + 0x7c) = param_2;
        if ((uVar7 & 1) != 0) {
          *(uint *)(param_1 + 8) = *(uint *)(param_1 + 8) & (*(uint *)(iVar3 + 0x78) ^ 0xffffffff);
        }
        iVar8 = *(int *)(iVar3 + 0x70);
        if (iVar3 == iVar8) {
          iVar9 = 0;
        }
        else {
          *(undefined4 *)(iVar8 + 0x74) = *(undefined4 *)(iVar3 + 0x74);
          if (iVar9 == iVar3) {
            iVar9 = iVar8;
          }
          *(undefined4 *)(*(int *)(iVar3 + 0x74) + 0x70) = *(undefined4 *)(iVar3 + 0x70);
        }
        *(int *)(param_1 + 0x14) = *(int *)(param_1 + 0x14) + -1;
        *(undefined4 *)(iVar3 + 0x68) = 0;
        *(undefined4 *)(iVar3 + 0x84) = 0;
        if (iVar2 == 0) {
          *(undefined4 *)(iVar3 + 0x70) = 0;
          iVar2 = iVar3;
          local_40 = iVar3;
        }
        else {
          *(int *)(local_40 + 0x70) = iVar3;
          *(undefined4 *)(iVar3 + 0x70) = 0;
          local_40 = iVar3;
        }
      }
      iVar4 = iVar4 + -1;
    } while (iVar4 != 0);
    *(int *)(param_1 + 0x10) = iVar9;
    puVar1 = PTR_DAT_10006ac0;
    wsr(0,uVar10);
    rsync();
    while (iVar2 != 0) {
      iVar6 = *(int *)(iVar2 + 0x70);
      if (*(int *)(iVar2 + 100) == 0) {
        *(undefined4 *)(iVar2 + 0x4c) = 0;
      }
      else {
        uVar11 = uVar11 & 0xffffcfff;
        FUN_1001bac4(iVar2 + 0x4c);
      }
      uVar10 = rsil(1);
      *(int *)puVar1 = *(int *)puVar1 + 1;
      wsr((char)uVar11,uVar10);
      rsync();
      uVar11 = uVar11 & 0xffffcfff;
      FUN_1001aac0(iVar2);
      uVar12 = (undefined1)uVar11;
      iVar2 = iVar6;
    }
    uVar10 = rsil(1);
    *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
    wsr(uVar12,uVar10);
    rsync();
    if ((*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) && (*(int *)PTR_DAT_10005d80 == 0)) {
      FUN_10018750();
    }
  }
  return 0;
}


