/* Function: 10016d23 FUN_10016d23 */


undefined4
FUN_10016d23(undefined4 param_1,undefined4 param_2,undefined4 param_3,int param_4,int param_5)

{
  undefined *puVar1;
  undefined4 unaff_retaddr;
  uint uVar2;
  int iVar3;
  undefined4 uVar4;
  int iVar5;
  int unaff_a8;
  int unaff_a9;
  int unaff_a10;
  int unaff_a11;
  int in_a12;
  int in_a13;
  int in_a14;
  int in_a15;
  undefined1 in_SAR;
  undefined1 in_EPC1;
  undefined1 in_EXCSAVE1;
  undefined1 in_INTSET;
  undefined1 in_INTENABLE;
  undefined1 in_EXCCAUSE;
  undefined4 local_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  undefined4 uStack_4;
  
  *(undefined4 *)PTR_DAT_10006a40 = param_3;
  uVar4 = rsr(in_EXCCAUSE);
  *(undefined4 *)PTR_DAT_10006a44 = uVar4;
  uVar4 = rsr(in_INTENABLE);
  *(undefined4 *)PTR_DAT_10006a48 = uVar4;
  uVar4 = rsr(in_INTSET);
  *(undefined4 *)PTR_DAT_10006a4c = uVar4;
  rsr(in_EPC1);
  *(undefined **)PTR_DAT_10006a50 = PTR_DAT_10006a50;
  *(undefined4 *)PTR_DAT_10006a54 = unaff_retaddr;
  puVar1 = PTR_DAT_10006a6c;
  iVar5 = *(int *)PTR_DAT_10006a40;
  iVar3 = rsr(in_EXCCAUSE);
  if (iVar3 != 5) {
    if (iVar3 == 4) {
      uVar4 = (*(code *)PTR_FUN_10006a58)(param_1,PTR_FUN_10006a58);
      return uVar4;
    }
    if (iVar3 != 9) {
      uVar4 = FUN_10016eb8(param_1,iVar3);
      return uVar4;
    }
    uVar4 = FUN_10016ef8();
    return uVar4;
  }
  *(undefined4 *)PTR_DAT_10006a6c = unaff_retaddr;
  *(undefined4 *)(puVar1 + 4) = param_1;
  uVar4 = rsr(in_SAR);
  iVar3 = rsr(in_EPC1);
  *(undefined4 *)(puVar1 + 8) = uVar4;
  uVar2 = iVar3 + 1;
  iVar3 = (uVar2 & 3) * -8 + 0x20;
  uVar2 = (uint)(*(int *)(uVar2 - (uVar2 & 3)) << 0x20 - iVar3) >> 0x1c;
  wsr((char)iVar3,*(undefined4 *)(puVar1 + 8));
  if (uVar2 < 8) {
    if (uVar2 < 4) {
      if (uVar2 < 2) {
        if (uVar2 != 0) goto LAB_10016ea1;
        iVar5 = *(int *)puVar1;
      }
      else if (uVar2 < 3) {
        iVar5 = *(int *)(puVar1 + 4);
      }
      else {
        iVar5 = rsr(in_EXCSAVE1);
      }
    }
    else if (uVar2 < 6) {
      if (4 < uVar2) {
LAB_10016e2c:
        iVar5 = param_4;
      }
    }
    else {
      iVar5 = param_5;
      if (6 < uVar2) goto LAB_10016e2c;
    }
  }
  else if (uVar2 < 0xc) {
    if (uVar2 < 10) {
      iVar5 = unaff_a9;
      if (uVar2 < 9) {
        iVar5 = unaff_a8;
      }
    }
    else {
      iVar5 = unaff_a11;
      if (uVar2 < 0xb) {
        iVar5 = unaff_a10;
      }
    }
  }
  else if (uVar2 < 0xe) {
    iVar5 = in_a13;
    if (uVar2 < 0xd) {
      iVar5 = in_a12;
    }
  }
  else {
    iVar5 = in_a15;
    if (uVar2 < 0xf) {
      iVar5 = in_a14;
    }
  }
  *(undefined4 *)(iVar5 + -0x10) = local_10;
  *(undefined4 *)(iVar5 + -0xc) = uStack_c;
  *(undefined4 *)(iVar5 + -8) = uStack_8;
  *(undefined4 *)(iVar5 + -4) = uStack_4;
LAB_10016ea1:
  iVar5 = rsr(in_EPC1);
  wsr(in_EPC1,iVar5 + 3);
  rsr(in_EXCSAVE1);
  rfe();
  return *(undefined4 *)(PTR_DAT_10006a6c + 4);
}


