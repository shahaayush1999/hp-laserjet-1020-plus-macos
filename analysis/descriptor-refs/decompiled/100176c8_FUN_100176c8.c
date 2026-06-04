/* Function: 100176c8 FUN_100176c8 */


void FUN_100176c8(int param_1)

{
  byte bVar1;
  undefined *puVar2;
  undefined *puVar3;
  uint uVar4;
  int iVar5;
  int *piVar6;
  uint uVar7;
  int iVar8;
  uint uVar9;
  undefined4 uVar10;
  
  uVar10 = rsil(1);
  iVar8 = *(int *)(param_1 + 0x38);
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
  if (iVar8 != 0) {
    iVar8 = *(int *)(param_1 + 0x2c);
    *(undefined4 *)(param_1 + 0x38) = 0;
    puVar2 = PTR_DAT_10006aa4;
    if (*(int *)(param_1 + 0x20) == param_1) {
      *(undefined4 *)(PTR_DAT_10006ab8 + iVar8 * 4) = 0;
      puVar3 = PTR_DAT_10006aa8;
      uVar7 = *(uint *)(param_1 + 0x40) ^ 0xffffffff;
      uVar9 = *(uint *)puVar2 & uVar7;
      uVar4 = *(uint *)PTR_DAT_10006aa8;
      *(uint *)puVar2 = uVar9;
      if (uVar4 != 0) {
        *(uint *)puVar3 = uVar4 & uVar7;
      }
      puVar2 = PTR_DAT_10006aa0;
      if ((uVar9 & 0xff) == 0) {
        if ((uVar9 & DAT_10005f74) == 0) {
          if ((uVar9 & DAT_10006a20) == 0) {
            if ((uVar9 & DAT_100066b8) == 0) {
              *(undefined4 *)PTR_DAT_10006aac = 0x20;
              *(undefined4 *)puVar2 = 0;
              wsr(0,uVar10);
              rsync();
              if (*(int *)PTR_DAT_10005d80 == 0) {
                FUN_10018750();
              }
              return;
            }
            uVar9 = uVar9 >> 0x18;
            iVar8 = 0x18;
          }
          else {
            uVar9 = uVar9 >> 0x10;
            iVar8 = 0x10;
          }
        }
        else {
          uVar9 = uVar9 >> 8;
          iVar8 = 8;
        }
      }
      else {
        iVar8 = 0;
      }
      bVar1 = PTR_DAT_10006ab0[uVar9 & 0xff];
      iVar5 = *(int *)PTR_DAT_10006aa0;
      *(uint *)PTR_DAT_10006aac = iVar8 + (uint)bVar1;
      puVar3 = PTR_DAT_10006aa8;
      if ((param_1 == iVar5) &&
         (iVar5 = *(int *)PTR_DAT_10006aa8,
         *(undefined4 *)puVar2 = *(undefined4 *)(PTR_DAT_10006ab8 + (iVar8 + (uint)bVar1) * 4),
         puVar2 = PTR_DAT_10006ac0, iVar5 != 0)) {
        *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
        wsr(0,uVar10);
        rsync();
        uVar10 = rsil(1);
        uVar9 = *(uint *)puVar3;
        *(int *)puVar2 = *(int *)puVar2 + -1;
        puVar2 = PTR_DAT_10006aa8;
        if ((uVar9 & 0xff) == 0) {
          if ((uVar9 & DAT_10005f74) == 0) {
            if ((uVar9 & DAT_10006a20) == 0) {
              uVar9 = uVar9 >> 0x18;
              iVar8 = 0x18;
            }
            else {
              uVar9 = uVar9 >> 0x10;
              iVar8 = 0x10;
            }
          }
          else {
            uVar9 = uVar9 >> 8;
            iVar8 = 8;
          }
        }
        else {
          iVar8 = 0;
        }
        iVar8 = *(int *)(PTR_DAT_10006ab8 + (iVar8 + (uint)(byte)PTR_DAT_10006ab0[uVar9 & 0xff]) * 4
                        );
        if (*(uint *)(iVar8 + 0x3c) <= *(uint *)PTR_DAT_10006aac) {
          *(int *)PTR_DAT_10006aa0 = iVar8;
          *(uint *)puVar2 = *(uint *)puVar2 & (*(uint *)(iVar8 + 0x40) ^ 0xffffffff);
        }
      }
    }
    else {
      *(undefined4 *)(*(int *)(param_1 + 0x20) + 0x24) = *(undefined4 *)(param_1 + 0x24);
      puVar3 = PTR_DAT_10006ab8;
      *(undefined4 *)(*(int *)(param_1 + 0x24) + 0x20) = *(undefined4 *)(param_1 + 0x20);
      puVar2 = PTR_DAT_10006aa8;
      piVar6 = (int *)(puVar3 + iVar8 * 4);
      if (*piVar6 == param_1) {
        uVar9 = *(uint *)PTR_DAT_10006aa8;
        *piVar6 = *(int *)(param_1 + 0x20);
        if (uVar9 != 0) {
          *(uint *)puVar2 = uVar9 & (*(uint *)(param_1 + 0x40) ^ 0xffffffff);
        }
        if (param_1 == *(int *)PTR_DAT_10006aa0) {
          *(undefined4 *)PTR_DAT_10006aa0 = *(undefined4 *)(puVar3 + *(int *)PTR_DAT_10006aac * 4);
        }
      }
    }
  }
  wsr(0,uVar10);
  rsync();
  if ((*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) && (*(int *)PTR_DAT_10005d80 == 0)) {
    FUN_10018750();
  }
  return;
}


