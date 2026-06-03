/* Function: 1001b770 FUN_1001b770 */


undefined4 FUN_1001b770(uint param_1)

{
  undefined4 uVar1;
  uint uVar2;
  
  uVar1 = rsil(0xf);
  uVar2 = rsr(0);
  wsr(0,param_1 | uVar2 & 0xfffffff0);
  return uVar1;
}


