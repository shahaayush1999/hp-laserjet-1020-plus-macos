/* Function: 10006f00 FUN_10006f00 */


void FUN_10006f00(uint param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  undefined4 uVar7;
  undefined1 uVar8;
  
  uVar8 = 0;
  iVar4 = FUN_1001bb5c();
  puVar3 = PTR_DAT_10005d0c;
  puVar2 = PTR_DAT_10005cf0;
  puVar1 = PTR_DAT_10005cec;
  if (*(int *)PTR_DAT_10005cf0 == 0) {
    return;
  }
  if ((*(uint *)PTR_DAT_10005d00 & param_1) == 0) {
    return;
  }
  uVar7 = rsil(1);
  iVar5 = FUN_10007430(*(undefined4 *)PTR_DAT_10005cf0,PTR_s__3d_0x_08x__8u_10005d08,
                       *(undefined4 *)PTR_DAT_10005cec,param_1,iVar4 - *(int *)PTR_DAT_10005d0c,
                       uVar7,param_4,uVar7);
  *(int *)puVar3 = iVar4;
  iVar4 = *(int *)puVar2;
  *(int *)puVar2 = iVar4 + iVar5;
  uVar6 = FUN_10007430(iVar4 + iVar5,param_2,param_3,param_4);
  puVar3 = PTR_DAT_10005cfc;
  if (0x80 < uVar6) {
    uVar6 = 0x80;
  }
  iVar5 = *(int *)puVar2;
  iVar4 = *(int *)puVar1;
  *(uint *)puVar2 = iVar5 + uVar6;
  *(int *)puVar1 = iVar4 + 1;
  if (*(uint *)puVar3 <= iVar5 + uVar6 + 0x100) {
    *(undefined4 *)puVar2 = *(undefined4 *)PTR_DAT_10005cf8;
  }
  wsr(uVar8,uVar7);
  rsync();
  return;
}


