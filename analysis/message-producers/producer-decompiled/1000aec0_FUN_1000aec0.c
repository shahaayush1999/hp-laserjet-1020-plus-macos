/* Function: 1000aec0 FUN_1000aec0 */


void FUN_1000aec0(void)

{
  undefined *puVar1;
  undefined4 local_50;
  undefined1 *puStack_4c;
  undefined1 auStack_40 [12];
  uint uStack_34;
  undefined1 auStack_30 [48];
  
  local_50 = 0xf;
  puStack_4c = auStack_30;
  FUN_10010f54(&local_50);
  auStack_30[0] = 3;
  FUN_10010fd0(&local_50);
  local_50 = 0xd;
  puStack_4c = auStack_30;
  FUN_10010f54(&local_50);
  auStack_30[0] = 0;
  FUN_10010fd0(&local_50);
  local_50 = 1;
  puStack_4c = auStack_40;
  FUN_10010f54(&local_50);
  uStack_34 = (uint)(byte)*PTR_DAT_100060a4;
  if (uStack_34 == 0) {
    uStack_34 = 1;
  }
  FUN_10010fd0(&local_50);
  local_50 = 10;
  puStack_4c = auStack_30;
  FUN_10010f54(&local_50);
  auStack_30[0] = 0;
  FUN_10010fd0(&local_50);
  local_50 = 9;
  puStack_4c = auStack_30;
  FUN_10010f54(&local_50);
  auStack_30[0] = 0x3c;
  FUN_10010fd0(&local_50);
  puVar1 = PTR_DAT_100060a8;
  *(undefined4 *)PTR_DAT_100060ac = 0x4b0;
  *(undefined4 *)puVar1 = 0x4b0;
  return;
}


