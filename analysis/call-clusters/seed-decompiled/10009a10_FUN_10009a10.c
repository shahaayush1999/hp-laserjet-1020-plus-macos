/* Function: 10009a10 FUN_10009a10 */


void FUN_10009a10(void)

{
  uint *puVar1;
  uint *puVar2;
  undefined *puVar3;
  undefined4 uVar4;
  uint uVar5;
  uint uVar6;
  
  puVar3 = PTR_DAT_10005fd0;
  memw();
  memw();
  *DAT_10005ea8 = *DAT_10005ea8 & 0xfffffff7;
  puVar2 = DAT_10005e70;
  puVar1 = DAT_10005e24;
  memw();
  memw();
  uVar6 = *DAT_10005e24;
  *(uint *)puVar3 = *DAT_10005e70 & 0x40;
  memw();
  memw();
  *puVar2 = *puVar2 | 0x80;
  memw();
  uVar5 = *puVar1;
  *(uint *)PTR_DAT_10005fd4 = uVar6 & 0x40;
  uVar4 = DAT_10005fd8;
  memw();
  *puVar1 = uVar5 | 0x80;
  FUN_100116ec(uVar4);
  return;
}


