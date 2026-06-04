/* Function: 1001aac0 FUN_1001aac0 */


undefined4 FUN_1001aac0(int param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  
  uVar7 = 0;
  uVar8 = rsil(1);
  iVar5 = *(int *)(param_1 + 0x38);
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
  puVar1 = PTR_DAT_10006ab8;
  if (iVar5 == 0) {
    if (*(int *)(param_1 + 0x30) != 0) {
      if (*(int *)(param_1 + 0x34) == 0) {
        uVar6 = *(uint *)(param_1 + 0x2c);
        *(undefined4 *)(param_1 + 0x30) = 0;
        iVar5 = *(int *)(puVar1 + uVar6 * 4);
        if (iVar5 == 0) {
          *(int *)(puVar1 + uVar6 * 4) = param_1;
          *(int *)(param_1 + 0x20) = param_1;
          puVar2 = PTR_DAT_10006aa4;
          *(int *)(param_1 + 0x24) = param_1;
          puVar1 = PTR_DAT_10006aa0;
          iVar5 = *(int *)PTR_DAT_10006aa0;
          *(uint *)puVar2 = *(uint *)puVar2 | *(uint *)(param_1 + 0x40);
          puVar2 = PTR_DAT_10006aac;
          if (iVar5 == 0) {
            *(int *)puVar1 = param_1;
            *(uint *)puVar2 = uVar6;
          }
          else if (uVar6 < *(uint *)PTR_DAT_10006aac) {
            uVar4 = *(uint *)(iVar5 + 0x3c);
            *(uint *)PTR_DAT_10006aac = uVar6;
            if (uVar6 < uVar4) {
              if (uVar4 != *(uint *)(iVar5 + 0x2c)) {
                *(uint *)PTR_DAT_10006aa8 = *(uint *)PTR_DAT_10006aa8 | *(uint *)(iVar5 + 0x40);
              }
              *(int *)puVar1 = param_1;
            }
          }
        }
        else {
          iVar3 = *(int *)(iVar5 + 0x24);
          *(int *)(iVar3 + 0x20) = param_1;
          *(int *)(iVar5 + 0x24) = param_1;
          *(int *)(param_1 + 0x24) = iVar3;
          *(int *)(param_1 + 0x20) = iVar5;
        }
      }
      else {
        *(undefined4 *)(param_1 + 0x34) = 0;
        *(undefined4 *)(param_1 + 0x30) = 3;
      }
    }
  }
  else if (1 < *(int *)(param_1 + 0x30) - 1U) {
    *(undefined4 *)(param_1 + 0x38) = 0;
    *(undefined4 *)(param_1 + 0x30) = 0;
  }
  wsr(0,uVar8);
  rsync();
  if ((*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) && (*(int *)PTR_DAT_10005d80 == 0)) {
    uVar7 = 1;
  }
  return uVar7;
}


