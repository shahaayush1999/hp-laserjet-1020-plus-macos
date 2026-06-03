/* Function: 1000c89c FUN_1000c89c */


undefined4 FUN_1000c89c(uint param_1,undefined4 param_2)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 local_40;
  undefined1 *puStack_3c;
  undefined4 uStack_30;
  undefined1 auStack_2c [44];
  
  iVar1 = FUN_1000d5b0(param_2,&uStack_30);
  uVar2 = 0;
  if (iVar1 != 0) {
    return 2;
  }
  if (uStack_30 < *(int *)(PTR_DAT_10006148 + (param_1 & 0xff) * 0x24 + 0x18)) {
    uVar2 = 3;
    uStack_30 = *(int *)(PTR_DAT_10006148 + (param_1 & 0xff) * 0x24 + 0x18);
  }
  if (*(int *)(PTR_DAT_10006148 + (param_1 & 0xff) * 0x24 + 0x1c) < uStack_30) {
    uVar2 = 3;
    uStack_30 = *(int *)(PTR_DAT_10006148 + (param_1 & 0xff) * 0x24 + 0x1c);
  }
  local_40 = 0xf;
  puStack_3c = auStack_2c;
  FUN_10010f54(&local_40);
  auStack_2c[0] = (undefined1)uStack_30;
  FUN_10010fd0(&local_40);
  return uVar2;
}


