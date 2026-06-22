
uint hp1020_usb_transfer_prepare_callback_candidate(int param_1,undefined4 param_2,uint param_3)

{
  int iVar1;
  
  if ((uint)(*(int *)(param_1 + 0x28) - *(int *)(param_1 + 0x24)) < param_3) {
    iVar1 = FUN_10013140(*(int *)(param_1 + 0x24) + param_3 + 0x100,1);
    FUN_1001b38c(iVar1,param_2,param_3);
    if (*(int *)(param_1 + 0x1c) != 0) {
      FUN_1001b38c(iVar1 + param_3,*(undefined4 *)(param_1 + 0x20),*(undefined4 *)(param_1 + 0x24));
      FUN_10013408(*(undefined4 *)(param_1 + 0x1c));
    }
    *(int *)(param_1 + 0x1c) = iVar1;
    *(uint *)(param_1 + 0x28) = *(int *)(param_1 + 0x24) + param_3 + 0x100;
  }
  else {
    FUN_1001b488(*(int *)(param_1 + 0x1c) + param_3,*(undefined4 *)(param_1 + 0x20));
    FUN_1001b38c(*(undefined4 *)(param_1 + 0x1c),param_2,param_3);
  }
  *(uint *)(param_1 + 0x24) = *(int *)(param_1 + 0x24) + param_3;
  *(undefined4 *)(param_1 + 0x20) = *(undefined4 *)(param_1 + 0x1c);
  return param_3;
}

