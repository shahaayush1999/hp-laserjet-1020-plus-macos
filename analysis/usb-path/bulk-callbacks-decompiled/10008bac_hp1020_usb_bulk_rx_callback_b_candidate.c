
undefined4
hp1020_usb_bulk_rx_callback_b_candidate(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  undefined4 *puVar4;
  
  puVar2 = PTR_DAT_10005e8c;
  iVar3 = FUN_100181a4(PTR_DAT_10005e8c,param_3);
  if (iVar3 != 0) {
    return 0;
  }
  FUN_100173c8(param_1,param_2);
  FUN_10008b78();
  puVar4 = (undefined4 *)FUN_10013140(0x20,1);
  puVar4[3] = puVar4 + 4;
  *puVar4 = 0;
  puVar4[4] = param_1;
  puVar4[5] = param_1;
  puVar4[6] = param_2;
  puVar1 = PTR_DAT_10005e10;
  puVar4[7] = 0;
  FUN_10013000(puVar1);
  puVar1 = PTR_DAT_10005e14;
  memw();
  iVar3 = *(int *)PTR_DAT_10005e14;
  memw();
  *DAT_10005e00 = *DAT_10005e00 & 0xfffffffd;
  if (iVar3 == 0) {
    *(undefined4 *)puVar1 = 1;
  }
  FUN_10018214(puVar2);
  return param_2;
}

