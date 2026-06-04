/* Function: 1001a950 FUN_1001a950 */


undefined4 FUN_1001a950(int param_1,uint param_2,undefined4 *param_3)

{
  undefined *puVar1;
  undefined *puVar2;
  uint uVar3;
  undefined4 uVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  undefined4 uVar8;
  
  if (0x1f < param_2) {
    return 0xf;
  }
  uVar8 = rsil(1);
  *param_3 = *(undefined4 *)(param_1 + 0x2c);
  puVar1 = PTR_DAT_10006aa4;
  if (*(int *)(param_1 + 0x30) == 0) {
    if (*(int *)(param_1 + 0x20) == param_1) {
      *(undefined4 *)(PTR_DAT_10006ab8 + *(int *)(param_1 + 0x2c) * 4) = 0;
      puVar2 = PTR_DAT_10006aa8;
      uVar6 = *(uint *)(param_1 + 0x40) ^ 0xffffffff;
      uVar7 = *(uint *)puVar1 & uVar6;
      uVar3 = *(uint *)PTR_DAT_10006aa8;
      *(uint *)puVar1 = uVar7;
      *(uint *)puVar2 = uVar3 & uVar6;
      *(int *)(param_1 + 0x40) = 1 << 0x20 - (0x20 - (param_2 & 0x1f));
      if ((uVar7 & 0xff) == 0) {
        if ((uVar7 & DAT_10005f74) == 0) {
          if ((uVar7 & DAT_10006a20) == 0) {
            if ((uVar7 & DAT_100066b8) == 0) {
              iVar5 = 0x20;
            }
            else {
              iVar5 = (byte)PTR_DAT_10006ab0[uVar7 >> 0x18] + 0x18;
            }
          }
          else {
            iVar5 = (byte)PTR_DAT_10006ab0[uVar7 >> 0x10 & 0xff] + 0x10;
          }
        }
        else {
          iVar5 = (byte)PTR_DAT_10006ab0[uVar7 >> 8 & 0xff] + 8;
        }
        *(int *)PTR_DAT_10006aac = iVar5;
      }
      else {
        *(uint *)PTR_DAT_10006aac = (uint)(byte)PTR_DAT_10006ab0[uVar7 & 0xff];
      }
    }
    else {
      if (*(int *)(PTR_DAT_10006ab8 + *(int *)(param_1 + 0x2c) * 4) == param_1) {
        *(int *)(PTR_DAT_10006ab8 + *(int *)(param_1 + 0x2c) * 4) = *(int *)(param_1 + 0x20);
        *(uint *)PTR_DAT_10006aa8 =
             *(uint *)PTR_DAT_10006aa8 & (*(uint *)(param_1 + 0x40) ^ 0xffffffff);
      }
      *(undefined4 *)(*(int *)(param_1 + 0x20) + 0x24) = *(undefined4 *)(param_1 + 0x24);
      *(undefined4 *)(*(int *)(param_1 + 0x24) + 0x20) = *(undefined4 *)(param_1 + 0x20);
      *(int *)(param_1 + 0x40) = 1 << 0x20 - (0x20 - (param_2 & 0x1f));
    }
    if (param_1 == *(int *)PTR_DAT_10006aa0) {
      if (*(int *)PTR_DAT_10006aac == 0x20) {
        uVar4 = 0;
      }
      else {
        uVar4 = *(undefined4 *)(PTR_DAT_10006ab8 + *(int *)PTR_DAT_10006aac * 4);
      }
      *(undefined4 *)PTR_DAT_10006aa0 = uVar4;
    }
    *(uint *)(param_1 + 0x2c) = param_2;
    puVar1 = PTR_DAT_10006ac0;
    *(uint *)(param_1 + 0x3c) = param_2;
    iVar5 = *(int *)puVar1;
    *(undefined4 *)(param_1 + 0x30) = 3;
    *(int *)puVar1 = iVar5 + 1;
    wsr(0,uVar8);
    rsync();
    FUN_1001aac0(param_1);
    if ((*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) && (*(int *)PTR_DAT_10005d80 == 0)) {
      FUN_10018750();
    }
  }
  else {
    *(uint *)(param_1 + 0x2c) = param_2;
    *(uint *)(param_1 + 0x3c) = param_2;
    *(int *)(param_1 + 0x40) = 1 << 0x20 - (0x20 - (param_2 & 0x1f));
    wsr(0,uVar8);
    rsync();
  }
  return 0;
}


