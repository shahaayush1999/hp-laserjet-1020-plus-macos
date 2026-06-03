/* Function: 10008034 FUN_10008034 */


void FUN_10008034(int param_1,undefined4 param_2,undefined4 param_3)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined4 uVar3;
  
  uVar3 = FUN_10013140(0x400,1);
  *(undefined4 *)(param_1 + 0x1c) = uVar3;
  *(undefined4 *)(param_1 + 0x20) = uVar3;
  *(undefined4 *)(param_1 + 0x28) = 0x400;
  FUN_1001b38c(param_2,uVar3,param_3);
  *(undefined4 *)(param_1 + 0x24) = param_3;
  *(undefined4 *)(param_1 + 0x40) = 0;
  *(undefined4 *)(param_1 + 0x44) = 0;
  *(undefined4 *)(param_1 + 0x50) = 0;
  *(undefined4 *)(param_1 + 0x48) = 0;
  puVar1 = PTR_LAB_10005dd0;
  *(undefined4 *)(param_1 + 0x4c) = 0;
  puVar2 = PTR_LAB_10005dd4;
  *(undefined **)(param_1 + 0x14) = puVar1;
  puVar1 = PTR_LAB_10005dd8;
  *(undefined **)(param_1 + 0xc) = puVar2;
  *(undefined **)(param_1 + 0x10) = puVar1;
  return;
}


