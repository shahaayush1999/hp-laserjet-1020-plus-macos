/* Function: 10017184 FUN_10017184 */


uint FUN_10017184(uint param_1)

{
  uint uVar1;
  uint uVar2;
  undefined4 uVar3;
  undefined1 in_INTENABLE;
  
  uVar3 = rsil(0xf);
  uVar1 = 1 << 0x20 - (0x20 - (param_1 & 0x1f));
  uVar2 = rsr(in_INTENABLE);
  wsr(in_INTENABLE,uVar2 | uVar1);
  wsr(0,uVar3);
  rsync();
  return uVar2 & uVar1;
}


